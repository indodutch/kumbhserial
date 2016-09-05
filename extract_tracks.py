#!/usr/bin/env python3
"""
Converts GPS row data to GeoJSON.

It reads the json file created by parse_excel.py and tries to
segment the set of data points into individual tracks. Two
files are output: tracks (GeoJSON LINESTRING) and point data
(GeoJSON Point). The first is useful for formatting, the second for
coloring and filtering.
"""
import json
import os
import time
from datetime import datetime
from pyproj import Proj, transform
import numpy as np


def timestamp(record):
    return time.mktime((
        record['year'], record['month'], record['day'],
        record['hour'], record['minute'], record['second'],
        0, 0, 0
    ))


def segment(records, segment_time_threshold=600):
    # when there is a break in data collection, consider the next part
    # as a new track
    path_segments = []
    prev_time = 0
    for record in records:
        record['timestamp'] = int(timestamp(record))
        record['weekDay'] = (datetime
                             .fromtimestamp(record['timestamp'])
                             .weekday())
        if (record['timestamp'] - prev_time >= segment_time_threshold or
                record['timestamp'] <= prev_time):
            path_segments.append([])
        prev_time = record['timestamp']
        path_segments[-1].append(record)

    return path_segments

def extract_tracks(input_directory, output_directory, segment_time_threshold=600):
    tracks = []
    points = []

    lat_lon_proj = Proj(init='epsg:4326')
    meter_proj = Proj(init='epsg:32642')

    for path, dirs, files in os.walk(input_directory):
        for file_name in files:
            if not file_name.endswith('.json'):
                continue

            with open(os.path.join(path, file_name)) as f:
                records = json.load(f)

            # when there is a break in data collection, consider the next part
            # as a new track
            path_segments = segment(records, segment_time_threshold)
            file_prefix = os.path.splitext(file_name)[0]

            for i, path_segment in enumerate(path_segments):
                coordinates = []
                prev_point_meter = None
                prev_timestamp = None

                for record in path_segment:
                    coord = [record['longitude'], record['latitude']]
                    meter_x, meter_y = transform(lat_lon_proj, meter_proj, coord[0], coord[1])
                    new_point_meter = np.array([meter_x, meter_y])
                    if prev_timestamp is None:
                        speed_computed_kmh = 0.0
                    else:
                        speed_computed_ms = np.linalg.norm(new_point_meter - prev_point_meter) / (record['timestamp'] - prev_timestamp)
                        speed_computed_kmh = speed_computed_ms*3600/1000
                    prev_point_meter = new_point_meter
                    prev_timestamp = record['timestamp']

                    points.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': coord,
                        },
                        'properties': {
                            'timestamp': record['timestamp'],
                            'speed': record['speed'],
                            'direction': record['direction'],
                            'numSatellites': record['numSatellites'],
                            'track': len(tracks) + 1,
                            'device': record['device'],
                            'meter_x': meter_x,
                            'meter_y': meter_y,
                            'speed_computed': speed_computed_kmh,
                        },
                    })
                    coordinates.append(coord)

                tracks.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates,
                    },
                    'properties': {
                        'id': len(tracks) + 1,
                        'device': path_segment[0]['device'],
                        'filename': file_prefix,
                    },
                })

    with open(os.path.join(output_directory, 'tracks.json'), 'w') as f:
        json.dump({
            'type': 'FeatureCollection',
            'features': tracks,
        }, f, separators=(',', ':'))

    with open(os.path.join(output_directory, 'points.json'), 'w') as f:
        json.dump({
            'type': 'FeatureCollection',
            'features': points,
        }, f, separators=(',', ':'))

extract_tracks(os.path.join('data', 'json'), os.path.join('data', 'geojson'))
