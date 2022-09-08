#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 16:40:56 2021

@author: Tom
"""


# --- imports ----

import crepe
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
import Analysers
from Analysers import AudioFile, Analyser
import TabBuilder
from scipy.io import wavfile
from TabDisplay import Ui_TabViewer
from time import sleep



#Main window class - the intial UI screen

class Ui_MainWindow(object):
      
    
    #Set up initial window
    def setupUi(self, MainWindow):
        
        
        #  ---   Set up window and buttons   ----
        
        #Window
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setMaximumSize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        #Title
        self.title = QtWidgets.QLabel(self.centralwidget)
        self.title.setGeometry(QtCore.QRect(262, 150, 400, 61))
        self.title.setText("TabMyPitchUp.")
        self.title.setFont(QFont('Times', 50))
        
        #Subtitle
        self.subTitle = QtWidgets.QLabel(self.centralwidget)
        self.subTitle.setGeometry(QtCore.QRect(278, 185, 400, 61))
        self.subTitle.setText("Automatic tabs from pitch tracking data")
        myFont=QtGui.QFont('Times', 15)
        myFont.setItalic(True)
        self.subTitle.setFont(myFont)
        
        #Buttons
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(320, 310, 181, 61))
        self.pushButton.setObjectName("pushButton")    
        self.pushButton2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton2.setGeometry(QtCore.QRect(320, 380, 181, 61))
        self.pushButton2.setObjectName("pushButton2")
        
        #Progress bar (initially hidden)
        self.progressBarWidget = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBarWidget.setGeometry(QtCore.QRect(320, 450, 181, 61))
        self.progressBarWidget.setVisible(False)
        self.loadingText = QLabel(self.centralwidget)
        self.loadingText.setGeometry(QtCore.QRect(320, 435, 181, 61))
        self.loadingText.setText("Analysing...")
        self.loadingText.setVisible(False)
        
        #Event handling for buttons
        self.pushButton.clicked.connect(lambda: self.upload(MainWindow))    
        self.pushButton2.clicked.connect(lambda: self.load(MainWindow))

        #Organise widgets
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "Upload audio"))
        self.pushButton2.setText(_translate("MainWindow", "Open .tab file"))
        
        
        
    #Upload audio file to the platform    
    def upload(self, MainWindow):
        name = QFileDialog.getOpenFileName(filter = "Audio File (*.wav)")
        if name == ('', ''):
            return
        else:
            #Display progress bar
            self.progressBarWidget.setVisible(True)
            self.loadingText.setVisible(True)
            sampleRate, audioData = wavfile.read(name[0])
            
            #Instantiate loading bar thread
            self.loadingBar = LoadingBar()
            self.loadingBar.setAudio(audioData)
            self.loadingBar.start()           
            self.loadingBar.progress.connect(self.updateProgress)
            
            #Instantiate audio analysis on separate thread
            self.analyseAudio = AnalyseAudio()
            self.analyseAudio.setAudioData(sampleRate, audioData)
            self.analyseAudio.start()
            self.analyseAudio.analysis.connect(self.analysisComplete)
            

    #Update the progress bar
    def updateProgress(self, value):
        self.progressBarWidget.setValue(value)
        
        
    #Receive audio information, call analyser class to process audio, then call goToTabViewer
    def analysisComplete(self, currentFile):
        tab = TabBuilder.Tab(Analyser(currentFile))
        MainWindow.close()
        self.goToTabViewer(tab)
        
        
    #Open tab window using a .tab file saved from a previous session
    def load(self, MainWindow):
        name = QFileDialog().getOpenFileName(filter = "Tab (*.tab)")
        if name == ('', ''):
            return
        else:
            with open(name[0], "r") as loadFile:
                tab = TabBuilder.Tab(str(loadFile.read()), "file")
                MainWindow.close()
                self.goToTabViewer(tab)
        
        
    #Open the tab display window
    def goToTabViewer(self, tab):
        self.tabViewer = QtWidgets.QMainWindow()
        self.ui = Ui_TabViewer()
        self.ui.setupUi(self.tabViewer, tab)
        self.tabViewer.show()



    
                
                
#Progress bar class

class LoadingBar(QThread):
    
    progress = pyqtSignal(int)   #Signal to update widget in main window
    
    #Function to commence progress bar filling up
    def run(self):
        for i in range(1, int ((len(self.audio)/44100)) + 1):         
            sleep(2.3) #Update progress every 2.3 seconds for each second of audio         
            self.progress.emit(i / int ((len(self.audio)/44100)) * 100)
            
            
    #Function to pass current audio file to current progress bar instance
    def setAudio(self, audio):
        self.audio = audio
        
        
#Analyse audio class - allows us to pass data to anlysers in a new thread
        
class AnalyseAudio(QThread):
    
    analysis = pyqtSignal(AudioFile) #Signal to pass data to Analyser class
    
    #Instantiate AudioFile class from analysers module
    def run(self):
        currentFile = AudioFile(self.sampleRate, self.audioData) 
        self.analysis.emit(currentFile)  
        
    #Receive audio information from mainWindow class
    def setAudioData(self, sampleRate, audioData):
        self.sampleRate = sampleRate
        self.audioData = audioData
                

        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    MainWindow.setWindowFlags(
        QtCore.Qt.WindowType.CustomizeWindowHint 
        | QtCore.Qt.WindowType.WindowCloseButtonHint 
        | QtCore.Qt.WindowType.WindowMinimizeButtonHint)
    
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
