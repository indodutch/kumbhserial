# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import time
import sys
import os
from .kumbhm_simple import DataRead


class KumbhMelaProcessor(object):
    def __init__(self, id_text='', save_dir='data/processed/'):
        if len(id_text) == 0:
            self.id = time.strftime("%Y%m%d-%H%M%S")
        else:
            self.id = id_text
        self.current_data = None
        self.error_cnt = 0
        self.file_cnt = 0
        self.line_nr = 0
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

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
            # maximum line address is 279620 with full 4MB data
            elif ((line[0] in ['0', '1', '2']) and
                  (self.current_data is not None)):
                if len(line) != 29:
                    # print(len(line), line)
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
            self.current_data.save(self.save_dir+'%s-%d.dat' % (self.id, self.file_cnt))
            self.file_cnt += 1
            self.current_data = None

    def handle_error(self, errcode=0):
        if self.current_data:
            self.current_data.error(errcode)
            self.save_data()


if __name__ == "__main__":
    fh = open(sys.argv[1], 'rb')
    proc = KumbhMelaProcessor()
    n_data = proc.process_file(fh)
    print('%d frames processed from %s' % (n_data, sys.argv[1]))
    fh.close()
