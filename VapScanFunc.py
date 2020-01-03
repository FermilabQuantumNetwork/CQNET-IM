"""
These are the functions you need to load in order to remotely control Bob's power supply.
Served as starter code for AliceScanFunc.py.

Requirements: Python3, packages listed below
OS: CentOS7
"""

import requests
import ast
from datetime import datetime, timedelta
import time
import numpy as np
import getpass
import os
import socket
import sys
import glob
import subprocess
from subprocess import Popen, PIPE
import pipes
from pipes import quote
import argparse
import pyvisa
import matplotlib.pyplot as plt


#Initiates remote control of power supply using VISA
def InitiateResource():
    VISAInstance=pyvisa.ResourceManager('@py')
    resourceName="USB0::65535::37168::602361010736720001::0::INSTR" #VISA name of power supply
    Resource = VISAInstance.open_resource(resourceName)
    print(Resource.query("*IDN?"))
    print("Set remote access")
    Resource.write("SYSTEM:REMOTE") #Set device to remote control
    return Resource


#Sets the channel number of the power supply
def SetChannel(Resource, ChannelNumber):
    if ChannelNumber == 1:
        cmd1 = "inst CH1"
    elif ChannelNumber == 2:
        cmd1 = "inst CH2"
    elif ChannelNumber == 3:
        cmd1 = "inst CH3"
    Resource.write(cmd1)

#Sets voltage of power supply for a given instrument, channel number, and channel voltage
def SetVoltage(Resource, ChannelNumber, ChVoltage):
    SetChannel(Resource,ChannelNumber)
    cmd2 = "volt " + str(ChVoltage) + "V"
    Resource.write(cmd2)
    return float(Resource.query("MEAS:VOLT?").rstrip())


#Creates array of voltages corresponding stairs of voltage: numSteps is the
#number of steps, where the step is a constant voltage for "sizeStep" iterations.
#If you plot out the array vs the index number (corresponding to time), the trace
#looks like stairs
def VoltageStairs(V1,V2,numSteps,sizeStep):
    vArray = np.linspace(V1,V2,numSteps)
    vStairs=[]
    for Vap in vArray:
        for s in range(sizeStep):
            vStairs.append(Vap)
    return np.array(vStairs)


#Creates array of voltages that corresponds to a voltage ramp. V1 is the starting
#voltage, V2 is the end voltage, and numV is the number of voltages to get from
#V1 to V2 in the ramp.
#If you plot out the array vs the index number (corresponding to time), the trace
#looks like a line from V1 to V2
def VoltageRamp(V1,V2,numV):
    return np.linspace(V1,V2,numV)


#Creates array of voltages where each element is V. "size" is the number of
#V's in the array.
#If you plot out the array vs the index number (corresponding to time), the trace
#looks like a horizontal line.
def VoltageConst(V,size):
    return V*np.ones(size)


#Turns off remote control of power supply
def DisableLVOutput(Resource):
    Resource.write("outp off")
    print("Disabled LV Output")
