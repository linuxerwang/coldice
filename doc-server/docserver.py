#!/usr/bin/python

import sys, os.path

sys.path.append('/usr/share/whoosh')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import ds.main
ds.main.main()

