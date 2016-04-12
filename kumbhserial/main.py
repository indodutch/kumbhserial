# -*- coding: utf-8 -*-
"""
Created on Fri Apr 08 12:13:28 2016

@author: Zoli
"""
import os
from .kumbhm_dumper import dumper_main
from .kumbhm_processor import KumbhMelaProcessor
import sys


def main(argv=sys.argv[1:]):
    dumpfile, port = dumper_main()
    if dumpfile:
        fid = os.path.basename(dumpfile).split('.')[0]
        proc = KumbhMelaProcessor(fid)
        fh = open(dumpfile, 'rb')
        n_data = proc.process_file(fh)
        fh.close()
        print('%d frames processed' % (n_data,))
        movepath = '../data/processed/raw/'
        if not os.path.exists(movepath):
            os.mkdir(movepath)
        newdumppath = movepath+os.path.basename(dumpfile)
        os.rename(dumpfile, newdumppath)
        print('backup saved to '+newdumppath)

if __name__ == "__main__":
    main()
