import serial

tty_name = '/dev/tty.BlueADC-DevB'

s = serial.Serial(port=tty_name, baudrate=9600)
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
            print count
            if count == 1024:
                i = 0 
                while i < count:
                    low = s.read(1)
                    high = s.read(1)
                    value = (ord(high[0]) * 256) + ord(low[0])
                    if (t == False):
                        k = value
                        t = True
                    if (t == True):
                        if (value != k):
                            print 'FAIL: ' + str(value) + ' ' + str(k)    
                    k += 1
                    if (k == 1024):
                        k = 0 
                    i += 1
                end_code = s.read(1)
