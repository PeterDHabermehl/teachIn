#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""fischertechnik App - Copyright (c) 2019 -- Peter Habermehl
"""

import sys, time, json
import ftduino_direct as ftd
import numpy as np
from TouchStyle import *
from TouchAuxiliary import *
from PyQt4 import QtCore, QtGui

DEVEL = False
FTD_VER = "1.3.3_en14"

HOSTDIR = os.path.dirname(os.path.realpath(__file__))
PROGDIR= os.path.join(HOSTDIR , "proglists")

if not os.path.exists(PROGDIR):
    os.mkdir(PROGDIR)

LAPOS = [    0,  900, 1000, 1200, 1325, 1450, 1500, 2600, 2800, 3050, 3200, 3350, 3425, 3500, 3650, 3700, 3800 ]
UUPOS = [ 1100, 1150, 2250, 2850, 3200, 3700, 3730, 3730, 3730, 3730, 3730, 3730, 3730, 3730, 3730, 3730, 3730 ]
ULPOS = [    0,    0,    0,    0,    0,    0,    0,    0,  800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 3650 ]

class QDblPushButton(QPushButton):
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clicked.emit)
        super().clicked.connect(self.checkDoubleClick)

    @pyqtSlot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start(250)

class FtcGuiApplication(TouchApplication):
    """Steuerung für Trainingsroboter mit 3 Steppern und Servo-Greifer
    """
    def __init__(self, args):
        super(FtcGuiApplication, self).__init__(args)
        
        # some variables
        self.a1pos = 0 # Axis 1: Rotational base
        self.a2pos = 0 # Axis 2: Upper arm
        self.a3pos = 0 # Axis 3: Lower arm
        self.a4pos = 10 # Axis 4: Servo gripper
        
        
        self.win = TouchWindow("TiCo")
        
        if self.win.width()>240:
            BIGDISPLAY = True
        else:
            BIGDISPLAY = False
        
        # Some tabs
        self.tabs = QTabWidget()
        
        # Tab 1:  direct control
        tab01 = QWidget()
        
        vbox = QVBoxLayout()
        
        hbox = QHBoxLayout()
        
        self.a1 = QPushButton("Ro")
        self.a1.setStyleSheet("QPushButton:checked { border-style: inset; background-color: orange }")
        self.a1.setCheckable(True)
        self.a1.setChecked(True)
        hbox.addWidget(self.a1)
        self.a2 = QPushButton("UA")
        self.a2.setStyleSheet("QPushButton:checked { border-style: inset; background-color: orange }")
        self.a2.setCheckable(True)
        self.a2.setChecked(False)
        hbox.addWidget(self.a2)
        self.a3 = QPushButton("LA")
        self.a3.setStyleSheet("QPushButton:checked { border-style: inset; background-color: orange }")
        self.a3.setCheckable(True)
        self.a3.setChecked(False)
        hbox.addWidget(self.a3)
        self.a4 = QPushButton("Gr") 
        self.a4.setStyleSheet("QPushButton:checked { border-style: inset; background-color: orange }")
        self.a4.setCheckable(True)
        self.a4.setChecked(False)
        hbox.addWidget(self.a4)
        
        self.a1.clicked.connect(self.axesClick)
        self.a2.clicked.connect(self.axesClick)
        self.a3.clicked.connect(self.axesClick)
        self.a4.clicked.connect(self.axesClick)
        
        vbox.addLayout(hbox)
        
        if BIGDISPLAY:
            self.dial = QDial()
            self.dial.setNotchesVisible(True)
            self.dial.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        else:
            self.dial = QSlider(Qt.Horizontal)
            
        self.dial.setMinimum(0)
        self.dial.setMaximum(6500)
        self.dial.setValue(0)
        self.dial.sliderReleased.connect(self.dialed)
        self.dial.valueChanged.connect(self.dialing)
        
        vbox.addWidget(self.dial)
           
        hbox = QHBoxLayout()
        
        self.lesser = QPushButton("  <  ")
        self.lesser.setAutoRepeat(True)
        self.lesser.setAutoRepeatInterval(5)
        self.lesser.clicked.connect(self.lesserClicked)
        hbox.addWidget(self.lesser)
        hbox.addStretch()
        
        self.number =QLineEdit()
        self.number.setReadOnly(True)
        self.number.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hbox.addWidget(self.number)
        hbox.addStretch()
        
        self.greater = QPushButton("  >  ")
        self.greater.setAutoRepeat(True)
        self.greater.setAutoRepeatInterval(5)
        self.greater.clicked.connect(self.greaterClicked)
        hbox.addWidget(self.greater)
        
        vbox.addLayout(hbox)
        
        #
        
        hbox = QHBoxLayout()
        self.home = QPushButton(">|<")
        self.home.clicked.connect(self.rob_home)
        hbox.addWidget(self.home)
        if BIGDISPLAY:
            self.allOff = QPushButton("ALL OFF")
        else:
            self.allOff = QPushButton("OFF")
            
        self.allOff.setStyleSheet("QPushButton { background-color: red}")
        self.allOff.clicked.connect(self.all_off)
        hbox.addWidget(self.allOff)
        self.add = QPushButton("Add")
        self.add.setStyleSheet("QPushButton { background-color: green}")
        self.add.clicked.connect(self.addToList)
        hbox.addWidget(self.add)
        
        vbox.addLayout(hbox)
        
        #
        tab01.setLayout(vbox)
        self.tabs.addTab(tab01,"Ctrl")
        
        #
        # Tab 2:  Position list
        #
        tab02 = QWidget()
        
        vbox = QVBoxLayout()
        #
        self.posList = QListWidget()
        if BIGDISPLAY:
            self.posList.setStyleSheet("font: 16pt Courier")
        else:
            self.posList.setStyleSheet("font: 12pt Courier")
        self.posList.itemDoubleClicked.connect(self.itmDblClicked)
        vbox.addWidget(self.posList)
        
        hbox = QHBoxLayout()
        self.itmUp = QPushButton(" /\ ")
        self.itmUp.clicked.connect(self.itmUpClicked)
        hbox.addWidget(self.itmUp)

        self.itmDn = QPushButton(" \/ ")
        self.itmDn.clicked.connect(self.itmDnClicked)
        hbox.addWidget(self.itmDn)
        
        if BIGDISPLAY:
            self.itmIn = QPushButton(" Ins ")
        else:
            self.itmIn = QPushButton(" + ")
        self.itmIn.clicked.connect(self.itmInClicked)
        hbox.addWidget(self.itmIn)
        
        self.itmCp = QPushButton(" Cp ")
        self.itmCp.clicked.connect(self.itmCpClicked)
        hbox.addWidget(self.itmCp)
        
        if BIGDISPLAY:
            self.itmRm = QDblPushButton(" Del ")
        else:
            self.itmRm = QDblPushButton("  -  ")
        self.itmRm.setStyleSheet("QPushButton { background-color: darkred}")
        self.itmRm.doubleClicked.connect(self.itmRmClicked)
        hbox.addWidget(self.itmRm)
        
        vbox.addLayout(hbox)
        
        tab02.setLayout(vbox)
        self.tabs.addTab(tab02,"List")

        #
        # Tab 3:  Operation
        #
        tab03 = QWidget()
        
        vbox = QVBoxLayout()
        
        vbox.addStretch()
        
        self.walkThrough = QPushButton(" Run ")
        self.walkThrough.setStyleSheet("QPushButton { background-color: green}")
        self.walkThrough.clicked.connect(self.walkThroughClicked)
        vbox.addWidget(self.walkThrough)
        
        vbox.addStretch()
        
        self.loadList = QPushButton("Load list")
        self.loadList.clicked.connect(self.loadListClicked)
        vbox.addWidget(self.loadList)
        
        self.saveList = QPushButton("Save list")
        self.saveList.clicked.connect(self.saveListClicked)
        vbox.addWidget(self.saveList)
        
        self.deleteList = QPushButton("Delete list")
        self.deleteList.setStyleSheet("QPushButton { background-color: darkblue}")
        self.deleteList.clicked.connect(self.deleteListClicked)
        vbox.addWidget(self.deleteList)
        
        vbox.addStretch()
        
        self.clearList = QDblPushButton("Clear list")
        self.clearList.setStyleSheet("QPushButton { background-color: darkred}")
        self.clearList.doubleClicked.connect(self.clearListClicked)
        vbox.addWidget(self.clearList)
        
        #
        tab03.setLayout(vbox)
        self.tabs.addTab(tab03,"Run")
    
        #
        #
        #
        
        self.win.setCentralWidget(self.tabs)
    
        
        #
        #
        #
        self.win.show()
        
        self.myftd=ftd.ftduino()
        
        if ((self.myftd.getDevice() == None) or (self.myftd.comm("ftduino_direct_get_version") != FTD_VER)) and not DEVEL:
            self.ftDuino_not_found()
            exit()
        
        self.myftd.ftduino.timeout=None
        
        self.exec_()

    def axesClick(self):
        sender = self.sender()

        if sender == self.a1 or sender == self.a2 or sender == self.a3 or sender == self.a4:
            self.a1.setChecked(False)
            self.a2.setChecked(False)
            self.a3.setChecked(False)
            self.a4.setChecked(False)
            sender.setChecked(True)
        
        if self.a1.isChecked():
            self.dial.setRange(0, 6500)
            self.dial.setValue(self.a1pos)
        elif self.a2.isChecked():
            self.dial.setRange(int(np.interp(self.a3pos, LAPOS, ULPOS)), int(np.interp(self.a3pos, LAPOS, UUPOS)))
            self.dial.setValue(self.a2pos)
        elif self.a3.isChecked(): 
            self.dial.setRange(int(np.interp(self.a2pos, UUPOS, LAPOS)), int(np.interp(self.a2pos, ULPOS, LAPOS)))
            self.dial.setValue(self.a3pos)
        elif self.a4.isChecked():
            self.dial.setRange(0, 100)
            self.dial.setValue(self.a4pos)
        self.dialed()
        
    def ftDuino_not_found(self):
        t=TouchMessageBox("Error", None)
        t.setCancelButton()
        t.setText("No ftDuino found\nor wrong software!")
        t.setTextSize(2)
        t.setBtnTextSize(2)
        t.setPosButton(QCoreApplication.translate("ecl","Okay"))
        (v1,v2)=t.exec_()
    
    def rob_home(self):
        self.myftd.comm("rob_home")
        self.myftd.comm("rob_grab 10")
        self.a1pos = 0
        self.a2pos = 0
        self.a3pos = 0
        self.a4pos = 10
        self.axesClick()
        
    def all_off(self):
        self.myftd.comm("rob_grab 10")
        self.a4pos = 10
        self.axesClick()
        self.myftd.comm("rob_off")
        
    def lesserClicked(self):
        self.dial.setValue(self.dial.value()-1)
        self.dialed()
    
    def greaterClicked(self):
        self.dial.setValue(self.dial.value()+1)
        self.dialed()
        
    def dialing(self):
        self.number.setText(str(self.dial.value()))
    
    def dialed(self):
        self.number.setText(str(self.dial.value()))
        if self.a1.isChecked():
            self.a1pos = self.dial.value()
            self.myftd.comm("rob_run "+str(self.a1pos)+" "+str(self.a3pos)+" "+str(self.a2pos))
        elif self.a2.isChecked():
            self.a2pos = self.dial.value()
            self.myftd.comm("rob_run "+str(self.a1pos)+" "+str(self.a3pos)+" "+str(self.a2pos))
        elif self.a3.isChecked():
            self.a3pos = self.dial.value()
            self.myftd.comm("rob_run "+str(self.a1pos)+" "+str(self.a3pos)+" "+str(self.a2pos))
        elif self.a4.isChecked():
            self.a4pos = self.dial.value()
            self.myftd.comm("rob_grab "+str(self.a4pos))
    
    def addToList(self):
        self.posList.addItem('{:3d}:{:5d}{:5d}{:5d}{:3d}'.format(self.posList.count()+1,self.a1pos,self.a2pos,self.a3pos,self.a4pos))
    
    def itmDblClicked(self):
        self.oldMcGrab = -1

        d = self.posList.item(self.posList.currentRow()).text().split()
        self.execStep(d, self.posList.currentRow())
        
        self.axesClick()
        
    def itmUpClicked(self):
        row=self.posList.currentRow()
        if row>0:
            i=self.posList.takeItem(row)
            self.posList.insertItem(row-1,i)
            self.posList.setCurrentRow(row-1)
    
    def itmDnClicked(self):
        row=self.posList.currentRow()
        if row<self.posList.count()-1:
            i=self.posList.takeItem(row)
            self.posList.insertItem(row+1,i)
            self.posList.setCurrentRow(row+1)
    
    def itmInClicked(self):
        fta=TouchAuxMultibutton("Command", self.win)
        fta.setButtons([ "Wait",
                         "User wait",
                         "Input wait",
                         "Home",
                         "All off"])
                      
        fta.setTextSize(3)
        fta.setBtnTextSize(3)
        (s,r)=fta.exec_() 
        
        if r == "Wait":
            t = TouchAuxKeyboard("Time [msec]","1000", self.win).exec_()  
            try:
                r = abs(int(t))
            except:
                r = 0
            if r != 0:
                self.posList.addItem("Cmd: Wait " + str(r) + " msec")
        elif r == "User wait":
            t = TouchAuxKeyboard("Message", "Press button to continue.", self.win).exec_()
            self.posList.addItem("Cmd: User_wait " + t)
        elif r == "Input wait":
            s,r=TouchAuxRequestInteger(
            "Input No.","Please select input to wait for:",
            4,
            4,
            8,"Okay",self.win).exec_()  
            if s:
                self.posList.addItem("Cmd: Input_wait " + str(r))
        elif r == "Home":
            self.posList.addItem("Cmd: Home")
        elif r == "All off":
            self.posList.addItem("Cmd: All_off")
    
    def itmCpClicked(self):
        if self.posList.count()>0:
            row=self.posList.currentRow()
            self.posList.insertItem(row+1,self.posList.item(row).text())
            self.posList.setCurrentRow(row+1)
    
    def itmRmClicked(self):
        return self.posList.takeItem(self.posList.currentRow())
    
    def walkThroughClicked(self):
        self.oldMcGrab = -1
                
        self.tabs.setCurrentIndex(1)
        self.posList.setCurrentRow(0)

        for ch in self.win.findChildren(QWidget,''):
            ch.setEnabled(False)
            
        self.processEvents()

        for i in range(0, self.posList.count()):
            self.processEvents()
            self.posList.setCurrentRow(i)
            self.processEvents()
            
            d = self.posList.item(i).text().split()
            self.processEvents()
            
            self.execStep(d, i)            
                    
        for ch in self.win.findChildren(QWidget,''):
            ch.setEnabled(True)           

        self.axesClick()
        self.myftd.comm("rob_off")
        
        
    def execStep(self, d, i):
        if d[0] != "Cmd:":
            self.myftd.comm("rob_run " + d[1] + " " + d[3] + " " + d[2])
            
            if int(d[4]) != self.oldMcGrab :
                self.oldMcGrab = int(d[4])
                self.myftd.comm("rob_grab " + d[4])
                time.sleep(0.5)
            self.a1pos = int(d[1])
            self.a2pos = int(d[2])
            self.a3pos = int(d[3])
            self.a4pos = int(d[4])
        elif d[1] == "Home":
            self.rob_home()
        elif d[1] == "All_off":
            self.all_off()
        elif d[1] == "Wait":
            time.sleep(float(d[2])/1000)
        elif d[1] == "User_wait":
            t=TouchMessageBox("User wait", self.win)
            t.setText(self.posList.item(i).text()[14:])
            t.setBtnTextSize(3)
            t.setPosButton("Continue")
            (r,s)=t.exec_()
        elif d[1] == "Input_wait":
            try:
                while int(self.myftd.comm("input_get i"+d[2])) == 0:
                    time.sleep(0.005)
            except:
                print("reading input failed")
    
    def loadListClicked(self):
        files = os.listdir(PROGDIR)        
        files.sort()
        
        if len(files) > 0:
            (s,r) = TouchAuxListRequester("Load","Program list",files,files[0],"Okay", self.win).exec_()
        
            if s:
                self.posList.clear()
                with open(os.path.join(PROGDIR, r), "r", encoding = "utf-8") as file:
                    line = file.readline()
                    while line:
                        self.posList.addItem(line[:-1])
                        line = file.readline()
                file.close()

    def saveListClicked(self):
        if self.posList.count()>0:
            filename = clean(TouchAuxKeyboard("Save","myProg",self.win).exec_(), 32)
            
            filename = os.path.join(PROGDIR, filename)
            
            s = "Yes"
            if os.path.exists(filename):
                t=TouchMessageBox("Warning", self.win)
                t.setCancelButton()
                t.setText("This file already\nexists!\nDo you want to\noverwrite it?")
                t.setBtnTextSize(2)
                t.setPosButton("Yes")
                t.setNegButton("No")
                (r,s)=t.exec_()
            
            if s == "Yes":
                with open(filename, "w", encoding = "utf-8") as file:
                    for i in range(0, self.posList.count()):
                        file.write(self.posList.item(i).text() + "\n")
                file.close()
        
    def deleteListClicked(self):
        files = os.listdir(PROGDIR)        
        files.sort()
        
        if len(files) > 0:
            (s,r) = TouchAuxListRequester("Delete","Program list",files,files[0],"Okay", self.win).exec_()
        
            if s:
                filename = os.path.join(PROGDIR, r)
                s = "Yes"
                if os.path.exists(filename):
                    t=TouchMessageBox("Warning", self.win)
                    t.setCancelButton()
                    t.setText("Do you really\nwant to permanently\ndelete this file?\n\n" + r)
                    t.setBtnTextSize(2)
                    t.setPosButton("Yes")
                    t.setNegButton("No")
                    (r,s)=t.exec_()
            
                if s == "Yes":
                    os.remove(filename)
            
    def clearListClicked(self):
        self.posList.clear()
        
def clean(text,maxlen):
    res=""
    valid="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-."
    for ch in text:
        if ch in valid: res=res+ch
    return res[:maxlen]
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
