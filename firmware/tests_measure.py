import serial
import threading
import time
import signal

cnt = 0
thread_work = True
s = serial.Serial('/dev/tty.BlueADC-DevB', 38400)

def handler(signal, frame):
        global thread_work
        thread_work = False
        s.close()
        
class measure_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global cnt
        global thread_work
        while thread_work:
            print "Data cout:" + str(cnt)
            cnt = 0
            time.sleep(1)

signal.signal(signal.SIGINT, handler)  
thread = measure_thread()
thread.start()    
s.timeout = 0.1
s.close()
t = False
k = 0 
s.open()

while True:
    code = s.read(1)
    if (len(code) == 1):
        if (ord(code) == 0x5c):
            count_low = s.read(1)
            if (len(count_low)) == 0:
                break
            count_high = s.read(1)
            if (len(count_high)) == 0:
                break
            count = (ord(count_high[0]) * 256) + ord(count_low[0])
            #print count
            if count == 1024:
                i = 0 
                while i < count:
                    low = s.read(1)
                    high = s.read(1)
                    value = (ord(high[0]) * 256) + ord(low[0])
                    cnt += 1
                    if (value == 0):
                        t = True
                    if (t == True):
                        if (value != k):
                            print 'FAIL: ' + value + ' ' + k    
                    k += 1
                    if (k == 1024):
                        k = 0 
                    i += 1
                end_code = s.read(1)
