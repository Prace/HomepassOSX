#!/bin/bash

# The MIT License (MIT)
#
# Copyright (c) 2014 Gian Marco Prazzoli
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# homepassOSX -- v. 1.0
# Script by Gian Marco Prazzoli
# Tested with OSX 10.9 and 10.10 (Mavericks and Yosemite)


import os, time, sys, sqlite3, signal, re
from random import shuffle
from optparse import OptionParser

TIMELIMIT = "28800" # 8 HOURS IN SEC, limit of MAC refresh
wifiregex = re.compile('wi\-?fi|airport', re.I) 


def get_wifi_mac():
    p = list(os.popen("networksetup -listallhardwareports"))
    for i, h in enumerate(p):
        if wifiregex.search(h):
            ret = tuple(map(lambda x: x.split()[-1], p[i+1:i+3]))
            print >> sys.stderr, "Using Wi-fi (%s) with original MAC address %s" % ret
            return ret
    print >> sys.stderr, "Couldn't find any Wi-fi hardware, exiting..."
    exit(0)


WNAME, ORIGINALMAC = get_wifi_mac()  #get global variables


def signal_handler(signal, frame):
        print('\n\nSaving changes to DB, restoring original MAC address and exiting...\n')
        conn.commit()
        conn.close()
        clean_setup()
        exit(1)


def clean_setup():
    os.system("sudo ifconfig %s lladdr %s" % (WNAME, ORIGINALMAC))
    os.system("sudo networksetup -setairportpower %s off" % WNAME)
    os.system("sudo networksetup -setairportpower %s on" % WNAME)


def cyclemacs(macs):
    tmp = options.numsec or 40
    for addr in macs:
        os.system("sudo networksetup -setairportpower %s off" % WNAME) #TURN OFF WIFI
        time.sleep(3)
        m = addr[1]
        os.system("sudo networksetup -setairportpower %s on" % WNAME) #TURN ON WIFI
        print >> sys.stderr, "Trying MAC %s ..." % (m),
        os.system("sudo ifconfig %s ether %s" % (WNAME, m)) #SPOOF MAC ADDRESS
        if options.manual:  
            raw_input(" press ENTER when ready")
        else:   
            time.sleep(tmp)
        c.execute("UPDATE MAC SET LASTUSED = strftime('%s','now') WHERE ID = " + str(addr[0]))    #SAVE NEW TIME!
        conn.commit() 
        print >> sys.stderr, "Changing MAC!"


parser = OptionParser()
parser.add_option("-s", action="store", type="int", dest="numsec", help="change MAC every NUMSEC seconds (default = 40sec)")
parser.add_option("-m", "--manual", action="store_true", help="manual mode, script will wait for user input before changing MAC address")
parser.add_option("-r", "--random", action="store_true", help="random mode, script will shuffle MAC addresses")
(options, args) = parser.parse_args()
signal.signal(signal.SIGINT, signal_handler)


conn = sqlite3.connect('MACs.sqlite3')
c = conn.cursor()
macs = c.execute("SELECT * FROM MAC WHERE strftime('%s','now') - LASTUSED > " + TIMELIMIT)
macs = list(macs)
if options.random:
    shuffle(macs)
cyclemacs(macs)  #START CYCLE
conn.close()   #CLOSE DB CONNECTION SAFELY

clean_setup()