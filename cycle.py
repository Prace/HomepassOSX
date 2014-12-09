import os, time, sys, sqlite3, signal
from random import shuffle
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-s", "--seconds", action="store_false", help="change MAC every 's' seconds (default = 40sec)")
parser.add_option("-m", action="store_true", help="manual mode, script will wait for input before changing MAC address")
parser.add_option("-w", action="store_false", help="connect to Nintendo World only MACs")
(options, args) = parser.parse_args()

conn = sqlite3.connect('MACs.sqlite3')
c = conn.cursor()
TIMELIMIT = "28800" # 8 HOURS IN SEC, limit of MAC refresh

def signal_handler(signal, frame):
        print('\nSaving changes to DB and exiting...')
        conn.commit();
        conn.close();
        exit(1)

def cyclemacs(macs):
    tmp = options.seconds or 40
    for addr in macs:
        os.system("sudo networksetup -setairportpower en0 off") #TURN OFF WIFI
        time.sleep(3)
        m = addr[1]
        os.system("sudo networksetup -setairportpower en0 on") #TURN ON WIFI
        print >> sys.stderr, "Trying MAC %s ..." % (m),
        os.system("sudo ifconfig en0 ether %s" % (m)) #SPOOF MAC ADDRESS
        if options.m:  
            raw_input(" press ENTER when ready")
        else:
            time.sleep(tmp)
        c.execute("UPDATE MAC SET LASTUSED = strftime('%s','now') WHERE ID = " + str(addr[0]))    #SAVE NEW TIME!
        conn.commit() 
        print >> sys.stderr, "Changing MAC!"

signal.signal(signal.SIGINT, signal_handler)
macs = c.execute("SELECT * FROM MAC WHERE strftime('%s','now') - LASTUSED > " + TIMELIMIT)
macs = list(macs)
shuffle(macs)

cyclemacs(macs)  #START CYCLE

conn.close()   #CLOSE DB CONNECTION SAFELY
