# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import time
import sys
import os
import base64

class KumbhMelaProcessor:
    def __init__(self, id_text=''):
        if len(id_text) == 0:
            self.id = time.strftime("%Y%m%d-%H%M%S")
        else:
            self.id = id_text
        self.current_data = None
        self.error_cnt = 0
        self.file_cnt = 0
        self.line_nr = 0
        self.savedir = 'data/processed/'
        if not os.path.exists(self.savedir):
            os.makedirs(self.savedir)
            
    def process_file(self, infile):
        start_cnt = self.file_cnt
        line = infile.readline()
        self.line_nr = 0
        while line:
            line = line.strip()
            if len(line) < 1:
                pass
            elif line[0] == '>':
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
            line = infile.readline()
            self.line_nr += 1
        return self.file_cnt-start_cnt
                
    def save_data(self):
        if self.current_data:
            if not self.current_data.OK:
                self.error_cnt += 1
                print('error %d: at line %d,\n\terror code: %d' % (self.error_cnt, self.line_nr, self.current_data.errcode))
#                print('\n'.join(self.serial_buffer[:self.serial_buffer_read_index]))
            self.current_data.save(self.savedir+'%s-%d.dat' % (self.id, self.file_cnt))
            self.file_cnt += 1
            self.current_data = None
            
    def handle_error(self, errcode=0):
        if self.current_data:
            self.current_data.error(errcode)
            self.save_data()
                
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
        
if __name__ == "__main__":
    fh = open(sys.argv[1], 'rb')
    proc = KumbhMelaProcessor()
    n_data = proc.process_file(fh)
    print('%d frames processed from %s' % (n_data, sys.argv[1]))
    fh.close()