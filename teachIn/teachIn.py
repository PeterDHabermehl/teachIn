#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""fischertechnik App - Copyright (c) 2019 -- Peter Habermehl
"""

import sys, time
import ftduino_direct as ftd
from TouchStyle import *
from TouchAuxiliary import *
from PyQt4 import QtCore, QtGui

DEVEL = True
FTD_VER = "1.3.3_enhanced"

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
        
        
        self.win = TouchWindow("TeachIn")
        
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
        
        self.dial = QDial()
        self.dial.setNotchesVisible(True)
        self.dial.setMinimum(0)
        self.dial.setMaximum(3500)
        self.dial.setValue(0)
        self.dial.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        self.allOff = QPushButton("ALL OFF")
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
        self.posList.setStyleSheet("font: 16pt Courier")
        vbox.addWidget(self.posList)
        
        hbox = QHBoxLayout()
        self.itmUp = QPushButton(" /\ ")
        self.itmUp.clicked.connect(self.itmUpClicked)
        hbox.addWidget(self.itmUp)

        self.itmDn = QPushButton(" \/ ")
        self.itmDn.clicked.connect(self.itmDnClicked)
        hbox.addWidget(self.itmDn)
        
        self.itmIn = QPushButton(" Ins ")
        self.itmIn.clicked.connect(self.itmInClicked)
        hbox.addWidget(self.itmIn)
        
        self.itmCp = QPushButton(" Cp ")
        self.itmCp.clicked.connect(self.itmCpClicked)
        hbox.addWidget(self.itmCp)
        
        self.itmRm = QPushButton(" Del ")
        self.itmRm.setStyleSheet("QPushButton { background-color: darkred}")
        self.itmRm.clicked.connect(self.itmRmClicked)
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
        
        vbox.addStretch()
        
        self.clearList = QPushButton("Clear list")
        self.clearList.setStyleSheet("QPushButton { background-color: darkred}")
        self.clearList.clicked.connect(self.clearListClicked)
        vbox.addWidget(self.clearList)
        
        #
        tab03.setLayout(vbox)
        self.tabs.addTab(tab03,"Oper")
        
    
        #
        #
        #
        self.win.setCentralWidget(self.tabs)
        
        #
        # 
        #
        
        self.myftd=ftd.ftduino()
        
        if ((self.myftd.getDevice() == None) or (self.myftd.comm("ftduino_direct_get_version") != FTD_VER)) and not DEVEL:
            self.ftDuino_not_found()
            return

        
        #
        #
        #
        self.win.show()
        self.exec_()

    def axesClick(self):
        sender = self.sender()
        if sender != self.home:
            self.a1.setChecked(False)
            self.a2.setChecked(False)
            self.a3.setChecked(False)
            self.a4.setChecked(False)
            sender.setChecked(True)
        
        if self.a1.isChecked():
            self.dial.setRange(0, 6500)
            self.dial.setValue(self.a1pos)
        elif self.a2.isChecked():
            self.dial.setRange(0, 3500)
            self.dial.setValue(self.a2pos)
        elif self.a3.isChecked(): 
            self.dial.setRange(0, 3500)
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
        self.myftd.comm("rob_off")
        self.myftd.comm("rob_grab 10")
    
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
                         "Input wait"])
                      
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
                
    def itmCpClicked(self):
        if self.posList.count()>0:
            row=self.posList.currentRow()
            self.posList.insertItem(row+1,self.posList.item(row).text())
            self.posList.setCurrentRow(row+1)
    
    def itmRmClicked(self):
        return self.posList.takeItem(self.posList.currentRow())
    
    def walkThroughClicked(self):
        oldMcGrab = -1
        
        self.tabs.setCurrentIndex(1)
        self.processEvents()
        

        for i in range(0, self.posList.count()):
            self.posList.setCurrentRow(i)
            self.processEvents()
            
            d = self.posList.item(i).text().split()
            
            if d[0] != "Cmd:":
                self.myftd.comm("rob_run " + d[1] + " " + d[3] + " " + d[2])
                
                if int(d[4]) != oldMcGrab :
                    oldMcGrab = int(d[4])
                    self.myftd.comm("rob_grab " + d[4])
                    time.sleep(0.5)
            elif d[1] == "Wait":
                time.sleep(float(d[2])/1000)
            elif d[1] == "User_wait":
                t=TouchMessageBox("User wait", self.win)
                t.setText(self.posList.item(i).text()[14:])
                t.setBtnTextSize(3)
                t.setPosButton("Continue")
                (r,s)=t.exec_()
    def loadListClicked(self):
        pass
    
    def saveListClicked(self):
        pass
    
    def clearListClicked(self):
        t=TouchMessageBox("Clear", self.win)
        t.setCancelButton()
        t.setText("Do you really\nwant to delete\nthe program list?")
        t.setBtnTextSize(2)
        t.setPosButton("Yes")
        t.setNegButton("No")
        (r,s)=t.exec_()
        
        if s == "Yes": self.posList.clear()
                
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
