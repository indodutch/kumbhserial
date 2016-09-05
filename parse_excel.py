"""
Converts Thinture GPS Excel sheets to json.

This increases the redundancy of the data, but also makes
it easier to read cross-platform.
"""
import xlrd
import json
import os


def parse_excel(input_directory, output_directory):
    for path, dirs, files in os.walk(input_directory):
        for file_name in files:
            if not file_name.endswith('.xlsx'):
                continue

            wb = xlrd.open_workbook(os.path.join(path, file_name))
            sh = wb.sheet_by_index(0)

            records = []
            for rownum in range(1, sh.nrows):
                row = sh.row_values(rownum)
                year, month, day = xlrd.xldate_as_tuple(row[2],
                                                        wb.datemode)[:3]
                hour, minute, second = xlrd.xldate_as_tuple(row[3],
                                                            wb.datemode)[3:]
                records.append({
                    'row': int(row[0]),
                    'device': row[1],
                    'year': year,
                    'month': month,
                    'day': day,
                    'hour': hour,
                    'minute': minute,
                    'second': second,
                    'latitude': row[4],
                    'longitude': row[5],
                    'speed': row[6],
                    'direction': row[7],
                    'numSatellites': int(row[8])
                })
            json_file_name = os.path.splitext(file_name)[0] + '.json'
            json_path = os.path.join(output_directory, json_file_name)
            with open(json_path, 'w') as f:
                json.dump(records, f, separators=(',', ':'))

parse_excel(os.path.join('data', 'raw'), os.path.join('data', 'json'))
