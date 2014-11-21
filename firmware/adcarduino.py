import sys
import time
from PySide import QtGui
from PySide.QtCore import QThread
from PySide import QtCore
import serial
from collections import deque
import sched
import time

tty_name = '/dev/ttyUSB0' 
data = deque([])

class Update(QThread):
    def __init__(self, parent, paintWidget):
        QtCore.QThread.__init__(self, parent)
        self.paintWidget = paintWidget
    def run(self):
        while 1:
            self.paintWidget.draw()
            time.sleep(0.01)

class Capture(QThread):
   
    def __init__(self, parent, paintWidget):
        QtCore.QThread.__init__(self, parent)
        self.flag = 1 
        self.stop_flag = 0 
        self.paintWidget = paintWidget
        self.thread = Update(None, self.paintWidget)
        self.thread.start()
    def open_port(self):
        self.s = serial.Serial(port=tty_name, baudrate=19200)
        self.s.timeout = 0.1
        if (self.s.isOpen()):
            self.s.close()
        self.s.open()
        self.flag = 1
        self.stop_flag = 0 
    def run(self):
        self.s.write(chr(0xfc))
        while self.flag:
            code = self.s.read(1)
            if (len(code) == 1):
                buffer_data = []
                if (ord(code[0]) == 0x5c):
                    count_low = self.s.read(1)
                    if (len(count_low)) == 0:
                            break
                    count_high = self.s.read(1)
                    if (len(count_high)) == 0:
                        break
                    count = (ord(count_high[0]) * 256) + ord(count_low[0])
                    j = 0 
                    sum = 0
                    k = 0
                    buffer_data = []
                    while (j < count):
                        data_low = self.s.read(1)
                        if (len(data_low)) == 0:
                            break
                        data_high = self.s.read(1)
                        if (len(data_high)) == 0:
                            break
                        data_value = (ord(data_high[0]) * 256) + ord(data_low[0])
                        #sum = sum + data_value
                        #if (k > 50):
                        #    sum = sum / 50
                        #    buffer_data.append(sum)
                        #    sum = 0 
                        #    k = -1
                        buffer_data.append(data_value)
                        j = j + 1
                        #k = k + 1
                    end_code = self.s.read(1)
                    if (len(end_code)) == 0:
                        break
                    if (len(end_code) == 1 and ord(end_code[0]) == 0xc5):
                        #print buffer_data
                        for i in buffer_data:
                            data.append(i)
                        #self.paintWidget.draw()
                        #while len(data) >= 1000:
                        #    data.popleft()

        self.stop_flag = 1

    def stop_reading(self):
        self.s.write(chr(0xcf))
        self.s.flush()
        self.flag = 0
        while (self.stop_flag == 0):
            pass
        self.s.close()

class PaintingWidget(QtGui.QWidget):
    def __init__(self):
        super(PaintingWidget, self).__init__()
        self.initWidget()
        self.points = deque([])
    def initWidget(self):
        self.resize(1000, 256)
    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        x = 0
        if len(data) > 2:
            self.points.append(data.popleft())
            self.points.append(data.popleft())
        l = list(self.points)
        while (x < len(l)-2):
            y1 = (((l[x] * 400.0) / 1024.0))
            y2 = (((l[x+1] * 400.0) / 1024.0))
            painter.drawLine(x, y1, x+1, y2)
            x = x + 1
        if (len(self.points) >= (1000 - 1)):
            self.points.popleft()
            self.points.popleft()
        painter.end()
    def draw(self):
        self.update()

class App(QtGui.QWidget):
    def __init__(self):
        super(App, self).__init__()
        self.toggle = 1
        self.initUI()
    def initUI(self):
        self.setWindowTitle("Simple ATmega ADC")
        startButton = QtGui.QPushButton("Start")
        startButton.clicked.connect(self.startClicked)
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(startButton)
        vbox = QtGui.QVBoxLayout()
        self.paintWidget = PaintingWidget()
        vbox.addLayout(hbox) 
        vbox.addWidget(self.paintWidget)
        self.setLayout(vbox)
        self.resize(1000,500)
        self.show()
    def startClicked(self):
        if (self.toggle == 1):
            data = deque([])
            self.thread = Capture(None, self.paintWidget)
            self.thread.open_port()
            self.thread.start()
            self.toggle = 0
            return 
        if (self.toggle == 0):
            self.thread.stop_reading()
            self.toggle  = 1
            data = deque([])
            return 

def main():
    app = QtGui.QApplication(sys.argv)
    application = App()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
