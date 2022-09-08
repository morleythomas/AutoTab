#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 16:40:56 2021

@author: Tom
"""

# --- imports ----
"""
import Analysers
from Analysers import Analyser
import matplotlib.pyplot as mpl
"""


#Tab class - creates data structures from analyser outputs that represent tabs

class Tab:       

    fret_positions = [         #Defines frequency values for each fret of each string
    [6, [82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63]],
    [5, [110.00, 116.54, 123.47, 130.81, 138.50, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.12, 329.63, 349.23]],
    [4, [146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.12, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16]],
    [3, [196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.12, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.24]],
    [2, [246.94, 261.63, 277.18, 293.66, 311.12, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.24, 659.25, 698.46, 739.99, 783.99]],
    [1, [329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.24, 659.25, 698.46, 739.99, 783.99, 830.61, 880.00, 932.33, 987.77, 1046.50]]   
    ]   
    
    
    #Constructor for new tab
    def __init__(self, *args):
   
        
        #Instance is created by constructFromFile or constructFromAudio function depending on input type       
        if len(args) == 1:
            #If input is .wav file (default setting)
            self.constructFromAudio(args[0])
        elif len(args) > 1:
            if (args[1] == "file"):
                #If input is .tab file
                self.constructFromFile(args[0])
            elif (args[1] == "audio"):
                #If input is .wav file
                self.constructFromAudio(args[0])
            else:
                #Raise exception if input is invalid
                raise Exception("Format not recognised: ", args[1])
            
            
            
    #Create instance using .tab file
    def constructFromFile(self, tab):    
        
        self.tabulation = [0.00, []];  #Initialise tab data structure
        
        #Iterate .tab file and create tab array
        cellLength = ""       
        lengthRead = False
        currentNote = []
        currentValue = ""
        count = 1
        for value in str(tab):
            if (not lengthRead):
                if value == 'x':
                    lengthRead = True
                else:
                    cellLength = cellLength + value
            else:
                self.cell_length = float(cellLength)
                self.tabulation[0] = self.cell_length
                if value == '(' or value == '\'' or value == ',' or value == ')':
                    pass
                else:
                    if value != '-':
                        currentValue = currentValue + value
                    if value == '-' and count == 3:
                        currentNote.append(float(currentValue))
                        self.tabulation[1].append(currentNote)
                        currentValue = ""
                        currentNote = []
                        count = 1
                    elif value == '-' and count != 3:
                        currentNote.append(int(currentValue))
                        currentValue = ""
                        count += 1



    #Create instance using Analyser instance
    def constructFromAudio(self, analyser): 

        #Initialise cell length and tab array
        self.cell_length = analyser.cell_length
        self.tabulation = [self.cell_length, []]
        
        #Variable to store the fret of the first note detected
        prevIndex = -1
    
        #Enumerate through analyser output
        for i, note in enumerate(analyser.analysis):
            
            noteLocations = []  #Array storing all fretboard locations of the current note
            currentFret = [0, 0, 0.0]
            
            #Search fretboard positions for appearances of the note
            for j, string in enumerate(self.fret_positions):
                for k, fret in enumerate(self.fret_positions[j][1]):
                    if note == fret:
                        currentFret = [string[0], k, i * self.cell_length]
                        noteLocations.append(currentFret)
                        

            #Append next element to tab array
            #If no note is present                  
            if len(noteLocations) < 1:
                self.tabulation[1].append([0, 0, 0.0])
            
            #If the note appears only once on the fretboard
            elif len(noteLocations) == 1:
                self.tabulation[1].append(noteLocations[0])
                if prevIndex < 0:
                    prevIndex = noteLocations[0][1]
                
                
            #If the note appears mulitple times on the fretboard
            else:           
                #Select the note that minimises the distance between frets of the chosen notes
                minDistanceNote = noteLocations[0]
                for i in range(1, len(noteLocations)):
                    if abs(noteLocations[i][1] - prevIndex) < abs(minDistanceNote[1] - prevIndex):
                        minDistanceNote = noteLocations[i]
                
                #Append note to tabulation array
                if prevIndex < 0:
                    prevIndex = (minDistanceNote[1])
                    self.tabulation[1].append(minDistanceNote)
                else:
                    self.tabulation[1].append(minDistanceNote)



    #Reformat data to be saved as .tab file
    def saveTab(self): 
        fileString = str(self.cell_length) + "x"       
        for i, note in enumerate(self.tabulation[1]):
            for j, value in enumerate(note):
                fileString = fileString + str(value) + "-"           
        return fileString
    
    

    #Output tab to console
    def printTab(self):
        for i in range(len(self.fret_positions)-1, -1, -1):
            row = "{}\t".format(self.fret_positions[i][0])
            for j in range(len(self.tabulation[1])):
                noNote = True
                for k, note in enumerate(self.tabulation[1]):                    
                    if note[0] == self.fret_positions[i][0] and note[2] == j*self.cell_length:
                        if note[1] < 10:
                            row += str(note[1]) + "  "
                        else:
                            row += str(note[1]) + " "
                        noNote = False
                        break
                if noNote:
                    row += "-- "
            print(row)
        print("\n")
         
        
        
    #Populate a string with data pertaining to a given string in the output tab
    #String lines are used to construct output tabs in TabDisplay class
    def genStringLine(self, string, start, lineLength):        
        outputString = "{}\t".format(string)
        
        for i in range(start, ((lineLength + start) if (lineLength + start) < len(self.tabulation[1]) else len(self.tabulation[1]))):
            noNote = True
            for j, note in enumerate(self.tabulation[1]):
                if note[0] == string and note[2] == i*self.cell_length:
                    if note[1] < 10:
                        outputString += str(note[1]) + "  "
                    else:
                        outputString += str(note[1]) + " "
                    noNote = False
                    break
            if noNote:
                outputString += "-- "
                
        return outputString
        
