# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 14:55:32 2016

@author: Zoli
"""

import serial
import time
import sys
import thread
from serial_tools import serial_ports

class KumbhMelaDumper:
    WAIT_FOR_DEVICE_TIMEOUT = 12
    def __init__(self, port, filename):
        try:
            self.comm = serial.Serial(port, 921600, timeout=1)
        except serial.SerialException as e:
            print(e)
            sys.exit()
        self.port = port
        self.run = True
        self.stopped = False
        self.file = open(filename, 'wb')
        self.recv_till = time.time()
        thread.start_new_thread(self.serial_recv_thread, ())
        thread.start_new_thread(self.heartbeat_thread, ())
            
    def serial_recv_thread(self):
        while self.run or time.time() < self.recv_till:
            line = self.comm.readline()
            self.file.write(line)
        print('read stopped')
        self.file.close()
        self.stopped = True
        
    def heartbeat_thread(self):
        while self.run:
            self.comm.write('@')
            time.sleep(1)
        print('heartbeat stopped')
            
    def stop(self):
        if self.run:
            self.recv_till = time.time() + self.WAIT_FOR_DEVICE_TIMEOUT
            self.run = False
        
def rundumper(port):
    quit_commands = ['q', 'quit']
    run = True
    print('Reading '+port)
    filename = 'data/dump'+port+time.strftime("%Y%m%d-%H%M%S")+'.txt'
    logger = KumbhMelaDumper(port, filename)
    while run:
        if sys.stdin.readline().strip().lower() in quit_commands:
            run = False
            print('Stopping '+port)
            logger.stop()
            while not logger.stopped:
                time.sleep(1)
            print('Stopped.')
    return run, filename
    
def dumper_main():
    quit_commands = ['q', 'quit']
    run = True
    fname = ''
    port = ''
    while run:
        ports = serial_ports()
        if len(ports) == 0:
            print('No serial device detected, please plug in bracelet.')
            if sys.stdin.readline().strip().lower() in quit_commands:
                run = False
            continue
        print('Pick a serial port:%s' % (' '.join(['\n%d: %s' % (i, ports[i]) for i in range(len(ports))]),))
        textin = sys.stdin.readline().strip().lower()
        if textin in quit_commands:
            run = False
        elif textin in [p.lower() for p in ports]:
            port = ports[[p.lower() for p in ports].index(textin)]
            run, fname = rundumper(port)
        else:
            try:
                index = int(textin)
                run, fname = rundumper(ports[index])
            except:
                print('Given port not in the list. Try again. (q or quit to quit)')
    return fname, port

if __name__ == "__main__":
    fname, _ = dumper_main()
    if fname:
        print('serial data written into '+fname)