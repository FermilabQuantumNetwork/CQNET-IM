import requests
import ast
from datetime import datetime
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
import time

#### OTSDAQ and Autopilot ####
ip_address = "192.168.155.1"
use_socket = 8000
RunFilename = '/home/otsdaq/otsdaq/srcs/otsdaq_cmstiming/Data_2018_07_July_fqnet/ServiceData/RunNumber/OtherRuns0NextRunNumber.txt'
ScanFilename = '/home/mhussain/InterFerDAQ/NextScanNumber.txt'
StopAutopilotFileName = '/home/mhussain/InterFerDAQ/StopAutopilot.sh'

### Voltage and Temperature Scan ###
#InitialVoltage = 1.7
#FinalVoltage = 1.7
#VoltageStep = 0.05
#VoltageSettleTime = 120
#ChannelNumber = 1
#SetTemp = 26.5
#LowVoltageControlFileName = '/home/mhussain/InterFerDAQ/LVControl.txt'
#VoltageScanDataFileName = '/home/mhussain/InterFerDAQ/VoltageScanDataRegistry/'
#IncludeLowVoltageFileName = '/home/mhussain/InterFerDAQ/IncludeLowVoltageFile.txt'

# #Qutag Filecomm
# IncludeQutagFileName = '/home/mhussain/InterFerDAQ/IncludeQutagFile.txt'
# QutagControlFileName = '/home/mhussain/InterFerDAQ/QutagControl.txt'
# QutagScanDataFileName = '/home/mhussain/InterFerDAQ/QutagScanDataRegistry/'
