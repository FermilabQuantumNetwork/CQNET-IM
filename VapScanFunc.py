import requests
import ast
from datetime import datetime, timedelta
import time
import numpy as np
import getpass
import os
import subprocess as sp
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

def InitiateResource():
    VISAInstance=pyvisa.ResourceManager('@py')
    #ResourceList=VISAInstance.list_resources()
    #print(ResourceList)
    #for index in range(len(ResourceList)):
    #    print("Device number " + str(index) + " - " + ResourceList[index])
    #DeviceNumber = input("Which device is the power supply? ")
    #resourceName=ResourceList[int(DeviceNumber)]
    resourceName="USB0::65535::37168::602361010736720001::0::INSTR"
    Resource = VISAInstance.open_resource(resourceName)#,write_termination='\n',read_termination='\r')
    print(Resource.query("*IDN?"))
    print("Set remote access")
    Resource.write("SYSTEM:REMOTE") #Set device to remote control
    return Resource

def SetChannel(Resource, ChannelNumber):
    if ChannelNumber == 1:
        cmd1 = "inst CH1"
    elif ChannelNumber == 2:
        cmd1 = "inst CH2"
    elif ChannelNumber == 3:
        cmd1 = "inst CH3"
    Resource.write(cmd1)
    #print("Set channel to "+str(ChannelNumber)+"\n")
#Safety check -- if true, then check that set voltage between 0 and 2.
def SetVoltage(Resource, ChannelNumber, ChVoltage):
    SetChannel(Resource,ChannelNumber)
    cmd2 = "volt " + str(ChVoltage) + "V"
    Resource.write(cmd2)
    return float(Resource.query("MEAS:VOLT?").rstrip())

def VoltageStairs(V1,V2,numSteps,sizeStep):
    vArray = np.linspace(V1,V2,numSteps)
    vStairs=[]
    for Vap in vArray:
        for s in range(sizeStep):
            vStairs.append(Vap)
    return np.array(vStairs)

def VoltageRamp(V1,V2,numV):
    return np.linspace(V1,V2,numV)

def VoltageConst(V,size):
    return V*np.ones(size)

def DisableLVOutput(Resource):
    Resource.write("outp off")
    #Resource.read()
    print("Disabled LV Output")
