# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
try:
    import thread
except ImportError:
    import _thread as thread
import threading
import base64
from .serial_tools import choose_serial_port


class KumbhMelaLogger(object):
    WAIT_FOR_DEVICE_TIMEOUT = 12
    WAIT_FOR_FINISH_READ = 2

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
        self.recv_till = time.time()
        self.read_till = time.time()
        self.serial_buffer = []
        self.serial_buffer_lock = threading.Lock()
        self.serial_buffer_read_index = 0
        thread.start_new_thread(self.serial_recv_thread, ())
        thread.start_new_thread(self.read_thread, ())
        thread.start_new_thread(self.heartbeat_thread, ())
                
    def save_data(self):
        if self.current_data:
            if not self.current_data.OK:
                self.error_cnt += 1
                print('%d: %d' % (self.error_cnt, self.current_data.errcode))
#                print('\n'.join(self.serial_buffer[:self.serial_buffer_read_index]))
            self.current_data.save('data/%s_%s-%d.dat' % (self.port,
                                    time.strftime("%Y%m%d-%H%M%S"), self.file_cnt))
            self.file_cnt += 1
            with self.serial_buffer_lock:
                self.serial_buffer = self.serial_buffer[self.serial_buffer_read_index:]
                print(len(self.serial_buffer))
            self.serial_buffer_read_index = 0
            self.current_data = None
            
    def serial_recv_thread(self):
        while self.run or time.time() < self.recv_till:
            line = self.comm.readline()
            if len(line) < 1:
                #nothing arrived within the timeout
                continue
            if line[-1] != '\n':
                #an incomplete line arrived before the timeout hit in
                line += self.comm.readline()
            line = line.strip()
#            if len(line) < 1:
#                #empty line somehow...
#                print('empty line')
#                continue
            with self.serial_buffer_lock:
                self.serial_buffer.append(line)
        
    def read_thread(self):
        while self.run or time.time() < self.read_till:
            with self.serial_buffer_lock:
                try:
                    line = self.serial_buffer[self.serial_buffer_read_index]
                except IndexError:
                    #data not ready
                    continue
                self.serial_buffer_read_index += 1
            if len(line) < 1:
                continue
            if line[0] == '>':
                self.save_data()
                self.current_data = DataRead(line[1:])
            elif (line[0] in ['0', '1', '2']) and (not self.current_data is None): #maximum line address is 279620 with full 4MB data
                if len(line) != 29:
                    #print(len(line), line)
                    self.handle_error(10)
                else:
                    try:
                        line_id = int(line[:6])
                        self.current_data.add_data(line_id, line[6:])
                    except ValueError:
                        self.handle_error(11)
            elif line[0] == '<':
                self.save_data()
            else:
                self.handle_error(12)
        print('read stopped')
        self.save_data()
        if self.serial_buffer_read_index != 0:
            print('serial read interrupted\nbuffer len: %d, read index: %d' % (len(self.serial_buffer), self.serial_buffer_read_index))
        self.stopped = True
        
    def heartbeat_thread(self):
        while self.run:
            self.comm.write('@')
            time.sleep(1)
        print('heartbeat stopped')
            
    def handle_error(self, errcode=0):
        if self.current_data:
            self.current_data.error(errcode)
            self.save_data()
            
    def stop(self):
        if self.run:
            self.recv_till = time.time() + self.WAIT_FOR_DEVICE_TIMEOUT
            self.read_till = self.recv_till + self.WAIT_FOR_FINISH_READ
            self.run = False
                
class DataRead:
    def __init__(self, device_id):
        self.id = device_id
        self.data=[[],[]]
        self.system = self.data[0]
        self.detections = self.data[1]
        self.OK = True
        self.errcode = -1
        
    def error(self, errcode=0):
        self.OK = False
        self.errcode = errcode
        
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
            self.error(1)
            return
            
        if len(self.data[is_detection]) > 0 and line_id > len(self.data[is_detection]):
            self.error(2)
            return
            
        try:
            ddata = base64.b64decode(data[1:]+'==')
        except TypeError:
            self.error(3)
            return
            
        if sum(bytearray(ddata))%256 != 0:
            self.error(4)
            
        while line_id > len(self.data[is_detection])-1:
            self.data[is_detection].append(chr(255)*15)

        self.data[is_detection][line_id] = ddata[1:]
        
def runlogger(port):
    run = True
    print('Reading '+port)
    logger = KumbhMelaLogger(port)
    while run:
        if sys.stdin.readline().strip().lower() in quit_commands:
            run = False
            print('Stopping '+port)
            logger.stop()
            while not logger.stopped:
                time.sleep(1)
            print('Stopped.')
    return run


if __name__ == "__main__":
    run = True
    try:
        while run:
            port = choose_serial_port()
            run = run_logger(port)
    except ValueError:
        print("Quit.")
    