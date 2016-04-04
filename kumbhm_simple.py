# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
import thread
import base64

class KumbhMelaLogger:
    def __init__(self, port):
        try:
            self.comm = serial.Serial(port, 921600)
        except serial.SerialException as e:
            print(e)
            sys.exit()
        self.run = True
        thread.start_new_thread(self.heartbeat_thread, ())
        self.current_data = None
        while self.run:
            line = self.comm.readline().strip()
            if len(line) < 1:
                continue
            if line[0] == '>':
                self.save_data()
                self.current_data = DataRead(line[1:])
            elif line[0] in ['0', '1', '2']: #maximum line address is 279620 with full 4MB data
                if len(line) < 29:
                    self.handle_error()
                try:
                    line_id = int(line[:6])
                    self.current_data.add_data(line_id, line[6:])
                except ValueError:
                    self.handle_error()
            elif line[0] == '<':
                self.save_data()
            else:
                self.handle_error()
                
    def save_data(self):
        if self.current_data:
            #printing instead of saving for now
            print(self.current_data)
            self.current_data = None
        
    def heartbeat_thread(self):
        while self.run:
            self.comm.write('@')
            time.sleep(1)
            
    def handle_error(self):
        if self.current_data:
            self.current_data.error()
                
class DataRead:
    def __init__(self, device_id):
        self.id = device_id
        self.data=[[],[]]
        self.system = self.data[0]
        self.detections = self.data[1]
        self.OK = True
        
    def error(self):
        self.OK = False
        
    def __str__(self):
        if self.OK:
            text = 'device_id: %s\nsystem:\n' % (self.id,)
            for line in range(len(self.system)):
                text += '%d:\t%s\n' % (line, base64.b64encode(self.system[line]))
            text += '\ndetections:\n'
            for line in range(len(self.detections)):
                text += '%d:\t%s\n' % (line, base64.b64encode(self.detections[line]))
            return text
        return 'Corrupted reading!!\n\n'
            
    def add_data(self, line_id, data):
        if data[0] == ':':
            is_detection = True
        elif data[0] == '-':
            is_detection = False
        else:
            self.error()
            return
            
        if len(self.data[is_detection]) > 0 and line_id > len(self.data[is_detection]):
            self.error()
            return
            
        try:
            ddata = base64.b64decode(data[1:]+'==')
        except TypeError:
            self.error()
            return
            
        while line_id > len(self.data[is_detection])-1:
            self.data[is_detection].append('')

        self.data[is_detection][line_id] = ddata

if __name__ == "__main__":
    logger = KumbhMelaLogger('COM5')
    