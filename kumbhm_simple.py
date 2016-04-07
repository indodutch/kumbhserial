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
from serial_tools import serial_ports

class KumbhMelaLogger:
    WAIT_FOR_DEVICE_TIMEOUT = 15
    def __init__(self, port):
        try:
            self.comm = serial.Serial(port, 921600, timeout=1)
        except serial.SerialException as e:
            print(e)
            sys.exit()
        self.port = port
        self.run = True
        self.stopped = False
        self.current_data = None        
        self.error_cnt = 0
        self.file_cnt = 0
        self.wait_till = time.time()
        thread.start_new_thread(self.read_thread, ())
        thread.start_new_thread(self.heartbeat_thread, ())
                
    def save_data(self):
        if self.current_data:
            if not self.current_data.OK:
                self.error_cnt += 1
                print(self.error_cnt)
            self.current_data.save('data/%s_%s-%d.dat' % (self.port,
                                    time.strftime("%Y%m%d-%H%M%S"), self.file_cnt))
            self.file_cnt += 1
            #printing instead of saving for now
#            print(self.current_data)
            self.current_data = None
        
    def read_thread(self):
        while self.run or time.time() < self.wait_till:
            line = self.comm.readline().strip()
            if len(line) < 1:
                continue
            if line[0] == '>':
                self.save_data()
                self.current_data = DataRead(line[1:])
            elif (line[0] in ['0', '1', '2']) and (not self.current_data is None): #maximum line address is 279620 with full 4MB data
                if len(line) != 29:
                    self.handle_error()
                else:
                    try:
                        line_id = int(line[:6])
                        self.current_data.add_data(line_id, line[6:])
                    except ValueError:
                        self.handle_error()
            elif line[0] == '<':
                self.save_data()
            else:
                self.handle_error()
        print('read stopped')
        self.stopped = True
        
    def heartbeat_thread(self):
        while self.run:
            self.comm.write('@')
            time.sleep(1)
        print('heartbeat stopped')
            
    def handle_error(self):
        if self.current_data:
            self.current_data.error()
            self.save_data()
            
    def stop(self):
        if self.run:
            self.wait_till = time.time() + self.WAIT_FOR_DEVICE_TIMEOUT
            self.run = False
                
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
#                text += '%d:\t%s\n' % (line, base64.b64encode(self.system[line]))
                text += '%d:\t%s\n' % (line, self.system[line])
            text += '\ndetections:\n'
            for line in range(len(self.detections)):
#                text += '%d:\t%s\n' % (line, base64.b64encode(self.detections[line]))
                text += '%d:\t%s\n' % (line, self.detections[line])
            return text
        return 'Corrupted reading!!\n\n'
        
    def save(self, fname):
        f = open(fname+'s', 'wb')
        for line in self.system:
            f.write(line)
        f.close()
        f = open(fname+'d', 'wb')
        for line in self.detections:
            f.write(line)
        f.close()
            
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
            
        if sum(bytearray(ddata))%256 != 0:
            self.error()
            
        while line_id > len(self.data[is_detection])-1:
            self.data[is_detection].append(chr(255)*15)

        self.data[is_detection][line_id] = ddata[1:]

if __name__ == "__main__":
    quit_commands = ['q', 'quit']
    run = True
    while run:
        ports = serial_ports()
        if len(ports) == 0:
            print('No serial device detected, please plug in bracelet.')
            if sys.stdin.readline().strip().lower() in quit_commands:
                run = False
            continue
        print('Pick a serial port: %s' % (' '.join(ports),))
        textin = sys.stdin.readline().strip().lower()
        if textin in quit_commands:
            run = False
        elif textin in [p.lower() for p in ports]:
            print('Reading '+textin)
            logger = KumbhMelaLogger(textin)
            while run:
                if sys.stdin.readline().strip().lower() in quit_commands:
                    run = False
                    print('Stopping '+textin)
                    logger.stop()
                    while not logger.stopped:
                        time.sleep(1)
                    print('Stopped.')
        else:
            print('Given port not in the list. Try again. (q or quit to quit)')
    