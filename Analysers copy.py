#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 16:22:19 2021

@author: Tom
"""

import numpy as np
import crepe
import statistics
import matplotlib.pyplot as plt
from scipy import signal



#Audio file class, produces CREPE representations
class AudioFile:        
    
    def __init__(self, sampleRate, audio):      
        self.audio = audio
        self.sampleRate = sampleRate
        self.time, self.frequency, self.confidence, self.activation = crepe.predict(self.audio, self.sampleRate, viterbi=True)



#Analyser class
class Analyser:     

    #Fraction of sample rate used to downsample data for analysis    
    time_scale = 100   
    
    #Define frequencies attributed to different notes
    note_frequencies = [82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 
                        174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.12, 329.63, 349.23, 
                        369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.24, 659.25, 698.46, 739.99, 
                        783.99, 830.61, 880.00, 932.33, 987.77, 1046.50]
    
    #Set default cell length to 0.25
    cell_length = 0.25   
    
    #Constructor function - produces representations of the data used in crafting tabs
    def __init__(self, audioFile):
        

        CompressorAnalyser(audioFile)   #Apply dynamic compression to the audio
        
        self.threshold = ThresholdAnalyser(audioFile)   #Eliminate data below threshold from consideration

        self.frequency = FrequencyAnalyser(audioFile)   #Analyse frequencies

        merge = []      #Vector holding merged output of analyser outputs produced above

        #Change cell_length if play speed is fast - adjust length of cells proportionately 
        idealCellLength = 1 / PlaySpeedAnalyser(audioFile, self.threshold).notesPerSec
        self.cell_length = idealCellLength if idealCellLength < self.cell_length else self.cell_length
        
        #Merge representations, and populate merge array
        for i in range(0, len(self.frequency.outputVector)):
            merge.append(self.threshold.outputVector[i] * self.frequency.outputVector[i])     
        
        #Downsample merge array
        merge = self.downSample(merge, int(self.cell_length * self.time_scale))
        
        #Generate pitch change representation & merge with other representations
        self.pitchChanges = PitchChangeAnalyser(merge)     
        for i, element in enumerate(merge):
            merge[i] = element * self.pitchChanges.outputVector[i]
        
        #Set analysis variable to contain final representation of audio
        self.analysis = merge
        
        
        
        
        
        
    #   -------      Helper functions         ---------
   
     
    
    def averageFrequency(self, frequency, index, chunkLength):   #Get average frequency over a given timefame

        #Get average frequency over given timeframe
        sumOfFreqs = 0.0
        count = 0
        
        for i in range (index, index + chunkLength):           
            if frequency[i] > 76.00 and frequency[i] < 1065.00: #Filter out frequencies that are too low/high to be guitar notes
                sumOfFreqs += frequency[i]
                count += 1
        if count < 1:
            averageFreq = 0
        else:
            averageFreq = sumOfFreqs / float(count)           

        #Round result to the nearest frequency attributed to a musical note
        roundedAverage = 0.0
        for i, freq in enumerate(self.note_frequencies):
            if abs(averageFreq - freq) < abs(averageFreq - roundedAverage):
                roundedAverage = freq
                
        return roundedAverage

    
    
    #Detect amplitudes above given frequency for given timeframe
    def pluckDetected(self, index, chunkLength):
        
        #Stereo audio
        if self.audioFile.audio[0].shape[0]:
            for i in range (index, index + chunkLength):
                if self.audioFile.audio[i][0] > self.threshold:
                    return 1
        #Mono audio
        else:
            for i in range (index, index + chunkLength):
                if self.audioFile.audio[i] > self.threshold:
                    return 1
        return 0

    #Calculate threshold in terms of amplitude
    def getMax(self):
        
        #Stereo audio
        if self.audioFile.audio[0].shape[0] > 1:
            maximum = self.audioFile.audio[0][0]
            for i in range(0, self.audioFile.audio.shape[0]):
                if self.audioFile.audio[i][0] > maximum:
                    maximum = self.audioFile.audio[i][0]
        #Mono audio
        else:
            maximum = self.audioFile.audio[0]
            for i in range(0, self.audioFile.audio.shape[0]):
                if self.audioFile.audio[i] > maximum:
                    maximum = self.audioFile.audio[i]
        
        return maximum
    
    #Downsample by a given factor
    def downSample(self, inputVector, factor):
        newVector = []
        for i in range(0, int(len(inputVector)/factor)):
            frequenciesAboveZero = []
            for j in range(i*factor, (i*factor) + factor):
                if inputVector[j] > 0.0:
                    frequenciesAboveZero.append(inputVector[j])
            if len(frequenciesAboveZero) > 0:
                newVector.append(statistics.mode(frequenciesAboveZero))
        return newVector






#       ---   Analyser classes   ---
    

#Threshold analyser
class ThresholdAnalyser(Analyser):
    
    threshold_factor = 0.25  #Percentage of maximum amplitude by which to determine threshold
    
    def __init__(self, audioFile):
   
        self.audioFile = audioFile
        maximumVolume = self.getMax()
        self.threshold = maximumVolume * self.threshold_factor
        print(maximumVolume)
        print(maximumVolume * self.threshold_factor)
        
        #Create output representation
        outputVector = np.zeros(int(self.audioFile.audio.shape[0]* self.time_scale / self.audioFile.sampleRate), dtype=(int))               
        for i in range(0, len(outputVector)):
            outputVector[i] = self.pluckDetected( i * int(self.audioFile.sampleRate/self.time_scale), int(self.audioFile.sampleRate/self.time_scale) )               
        
        self.outputVector = outputVector
        
        
    #Create new representation with custom threshold factor
    def changeThreshold(self, newFactor):        
        self.threshold = self.getThreshold(newFactor)
        outputVector = np.zeros(int(self.audioFile.audio.shape[0]* self.time_scale / self.audioFile.sampleRate), dtype=(int))                
        for i in range(0, len(outputVector)):
            outputVector[i] = self.pluckDetected( i * int(self.audioFile.sampleRate/self.time_scale), int(self.audioFile.sampleRate/self.time_scale) )
        self.outputVector = outputVector
        
        
    #Override downsample method to work with threshold data
    def downSample(self, factor):   #Overide downsample in analyser class to work with binary array
        newVector = []
        for i in range(0, int(len(self.outputVector)/factor)):
            currentSum = 0
            for j in range(i*factor, (i*factor) + factor):
                currentSum += self.outputVector[j]
            if currentSum/factor < 0.5:
                newVector.append(0)
            else:
                newVector.append(1)
        return newVector
        
    
    
#Frequency analyser
class FrequencyAnalyser(Analyser):
    
    def __init__(self, audioFile):    
        self.audioFile = audioFile
        
        #Create representation
        outputVector = np.zeros(int(self.audioFile.audio.shape[0]* self.time_scale / self.audioFile.sampleRate), dtype=(float))                
        for i in range(0, len(outputVector)):
            outputVector[i] = self.averageFrequency(self.audioFile.frequency, i * int((1/self.audioFile.time[1]) / self.time_scale), int((1/self.audioFile.time[1]) / self.time_scale))           

        self.outputVector = outputVector

        

#Pitch change analyser
class PitchChangeAnalyser(Analyser):
    
    def __init__(self, inputFrequencies):
        
        self.inputFrequencies = inputFrequencies
        
        #Create array of 0s for every 0.01 interval in the audio clip
        outputVector = [1]

        #If a change in pitch is detected, set the current element in outputVector to 1
        currFreq = self.inputFrequencies[0]
        for i in range(1, len(inputFrequencies)):
            currFreq = self.inputFrequencies[i]
            if currFreq != self.inputFrequencies[i-1]:
                outputVector.append(1)
            else:
                outputVector.append(0)

        self.outputVector = outputVector
        
        
        
#Compressor
class CompressorAnalyser(Analyser):
    
    compression_factor = 8  #Variable to determine intensity of compression process 
    
    def __init__(self, audioFile):
        self.audioFile = audioFile
        maximumVolume = self.getMax()
        
        if self.audioFile.audio[0].shape[0] > 1:  #Stereo compression
            for i in range(len(audioFile.audio)):
                audioFile.audio[i][0] = (audioFile.audio[i][0] + abs( audioFile.audio[i][0] - maximumVolume ) / self.compression_factor)
        else:                                    #Mono compression
            for i in range(len(audioFile.audio)):
                audioFile.audio[i] = (audioFile.audio[i] + abs( audioFile.audio[i] - maximumVolume ) / self.compression_factor)
            
        
        
#PlaySpeed analyser
class PlaySpeedAnalyser(Analyser):
    
    #Determine playing speed based on the regularity of audio exceeding threshold
    def __init__(self, audioFile, thresholdAnalyser):
        self.notesPerSec = sum(thresholdAnalyser.outputVector) / audioFile.audio.shape[0] / audioFile.sampleRate
    
    
    
    
    
    
    #      -----     Unused algorithms   ---------    
    
    
    
    
#           -------        Peak picking analyser not in use          -----------
class PeakAnalyser(Analyser):
    
    def __init__(self, audioFile):
        #Get maximum value
        print(audioFile.audio)
        magnitudes = []
        
        maximum = 0
        for i, value in enumerate (audioFile.audio):
            magnitudes.append(value[0])
            if value[0] > maximum:
                maximum = value[0]
                
        #Find peaks using 80% of max value as prominence
        peaks, x = signal.find_peaks(magnitudes, distance=(int(audioFile.sampleRate/10)), threshold=(maximum*0.01))
        
        for i in peaks:
            print(i / audioFile.sampleRate)
        print(len(peaks))
        print(peaks)
        
        self.totalPeaks = len(peaks)
        
    
    
#       ------      NoiseAnalyser not being used        --------
class NoiseAnalyser(Analyser):
    
    def Analyse(thresholdAnalyser):
        
        total = 0
        
        for i in thresholdAnalyser.outputVector:
            total += i
            
        if total > len(thresholdAnalyser.outputVector)*0.9:
            thresholdAnalyser.changeThreshold(0.5)
            return thresholdAnalyser
        else:
            return thresholdAnalyser
        
    
