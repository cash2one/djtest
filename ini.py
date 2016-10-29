#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    cd=os.getcwd()
    for app in ['accounts','jiangan','pay']:
        cdir=cd+'/'+app+'/migrations'
        if not os.path.exists(cdir):
            os.mkdir(cdir)
        open(cdir+'/__init__.py','w',encoding='u8')
