#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 16:40:56 2021

@author: Tom
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from scipy.io import wavfile
from Analysers import Analyser, AudioFile
import TabBuilder
from time import sleep



#TabViewer class - window displaying tab output to user

class Ui_TabViewer(object):
    
    
    #Function that inserts tabs into the window
    def insertTab(self):
        
        #Define UI widgets
        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 1191, 101))
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.groupBoxLayout = QVBoxLayout()
        
        #For loop creating new line evry 68 cells
        self.lineSegments = []
        for i in range(int (len( self.tabBuilder.tabulation[1] ) / 48 ) + 1):
            TabLineSegment(self, i)         
        for line in self.lineSegments:
            self.groupBoxLayout.addWidget(line)
            
        self.groupBox.setLayout(self.groupBoxLayout)
        self.scrollArea.setWidget(self.groupBox)
        
        
    #Setup tab window
    def setupUi(self, MainWindow, tab):
        
        #Define window properties
        MainWindow.setObjectName("TabViewer")
        MainWindow.setWindowFlags(
            QtCore.Qt.WindowType.CustomizeWindowHint 
            | QtCore.Qt.WindowType.WindowCloseButtonHint 
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        MainWindow.resize(1270, 480)
        MainWindow.setMaximumSize(1270, 480)
        
        #Populate with widgets
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(30, 30, 1211, 321))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1207, 317))
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(30, 370, 91, 31))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(130, 370, 81, 31))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(220, 370, 81, 31))
        self.pushButton_3.setObjectName("pushButton_3")
        self.title = QtWidgets.QLabel(self.centralwidget)
        self.title.setGeometry(QtCore.QRect(870, 370, 400, 61))
        self.title.setText("TabMyPitchUp.")
        self.title.setFont(QFont('Times', 50))
        
        #Progress bar (initially hidden)
        self.progressBarWidget = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBarWidget.setGeometry(QtCore.QRect(42, 420, 260, 31))
        self.progressBarWidget.setVisible(False)
        self.loadingText = QLabel(self.centralwidget)
        self.loadingText.setGeometry(QtCore.QRect(42, 405, 91, 31))
        self.loadingText.setText("Analysing...")
        self.loadingText.setVisible(False)
                    
        #Produce output on screen              
        self.tabBuilder = tab
        self.insertTab()
        
        #Event handling for buttons
        self.pushButton.clicked.connect(self.saveTab)
        self.pushButton_2.clicked.connect(self.uploadNew)
        self.pushButton_3.clicked.connect(self.loadTab)
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1270, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("TabViewer", "TabViewer"))
        self.pushButton.setText(_translate("MainWindow", "Save"))
        self.pushButton_2.setText(_translate("MainWindow", "Upload"))
        self.pushButton_3.setText(_translate("MainWindow", "Open"))
        


    #Function to upload new audio file        
    def uploadNew(self):
        #Allow user to select .wav from files
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
            
            #Instantiate audio analysis
            self.analyseAudio = AnalyseAudio()
            self.analyseAudio.setAudioData(sampleRate, audioData)
            self.analyseAudio.start()
            self.analyseAudio.analysis.connect(self.analysisComplete)
        
        
    #Function to upload progress bar widget using signal from progress bar thread
    def updateProgress(self, value):
        self.progressBarWidget.setValue(value)
        
        
    #Take audio file data from AnalyseAudio thread, to create analysis & new tabb
    def analysisComplete(self, currentFile):
        self.tabBuilder = TabBuilder.Tab(Analyser(currentFile))
        self.insertTab()
        self.progressBarWidget.setVisible(False)
        self.loadingText.setVisible(False)
        
    
    
    #Function to save current tab as .tab file
    def saveTab(self):
        name = QFileDialog.getSaveFileName(filter = 'Tab (*.tab)')
        if name == ('', ''):
            return
        else:
            saveFile = open(name[0], "w")
            saveFile.write( self.tabBuilder.saveTab() )
            saveFile.close()
        
        
        
    #Function to load previously saved .tab file
    def loadTab(self): 
        name = QFileDialog().getOpenFileName(filter = "Tab (*.tab)")
        if name == ('', ''):
            return
        else:
            with open(name[0], "r") as loadFile:
                self.tabBuilder = TabBuilder.Tab(str(loadFile.read()), "file")
                self.insertTab()
        



#  --- LoadingBar & AnalyseAudio classes to be instantiated on different threads --- 

#Progress bar class
class LoadingBar(QThread):
    progress = pyqtSignal(int)   
    def run(self):
        for i in range(1, int ((len(self.audio)/44100)) + 1):
            sleep(2.2)
            self.progress.emit(i / int ((len(self.audio)/44100)) * 100)         
    def setAudio(self, audio):
        self.audio = audio
        
        
#Analyse audio class   
class AnalyseAudio(QThread):
    analysis = pyqtSignal(AudioFile)
    def run(self):
        currentFile = AudioFile(self.sampleRate, self.audioData) #AudioFile class from analysers module
        self.analysis.emit(currentFile)  
    def setAudioData(self, sampleRate, audioData):
        self.sampleRate = sampleRate
        self.audioData = audioData
        
        
        
        
        
#Class to produce lines of the output tab
class TabLineSegment():
    
    line_length = 46    #Max length of each line
    
    def __init__ (self, host, currentLine):        

        #Create six lines (for each string)
        self.label = QtWidgets.QLabel()
        self.label_2 = QtWidgets.QLabel()
        self.label_3 = QtWidgets.QLabel()
        self.label_4 = QtWidgets.QLabel()
        self.label_5 = QtWidgets.QLabel()
        self.label_6 = QtWidgets.QLabel()
        tabLineFont = QFont( "Courier" )
        self.label.setFont(tabLineFont)
        self.label_2.setFont(tabLineFont)
        self.label_3.setFont(tabLineFont)
        self.label_4.setFont(tabLineFont)
        self.label_5.setFont(tabLineFont)
        self.label_6.setFont(tabLineFont)
    
        #Fetch data from Tab object
        self.label.setText(host.tabBuilder.genStringLine(1, self.line_length * currentLine, self.line_length))
        self.label_2.setText(host.tabBuilder.genStringLine(2, self.line_length * currentLine, self.line_length))
        self.label_3.setText(host.tabBuilder.genStringLine(3, self.line_length * currentLine, self.line_length))
        self.label_4.setText(host.tabBuilder.genStringLine(4, self.line_length * currentLine, self.line_length))
        self.label_5.setText(host.tabBuilder.genStringLine(5, self.line_length * currentLine, self.line_length))
        self.label_6.setText(host.tabBuilder.genStringLine(6, self.line_length * currentLine, self.line_length))
    
        #Add each string to the current line
        host.lineSegments.append(self.label)
        host.lineSegments.append(self.label_2)
        host.lineSegments.append(self.label_3)
        host.lineSegments.append(self.label_4)
        host.lineSegments.append(self.label_5)
        host.lineSegments.append(self.label_6)
        
        #Add spaces below for formatting
        host.lineSegments.append(QtWidgets.QLabel(""))
        host.lineSegments.append(QtWidgets.QLabel(""))
        
        
    def close(self):
        self.groupBox.close()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_TabViewer()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
