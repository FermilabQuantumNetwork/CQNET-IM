"""
This script maximizes Bob's IM extinction ratio by minimizing the IM's output
optical power and prevents drifting.
It scans over the DC Bias and ER Tuning voltages for Bob's intensity modulator (IM) and
finds the voltages corresponding to the minimum output power, then
periodically does nested fine range scan to find and keep the IM at min power.
Ex: For each voltage in a scan range for ER Tuning pin, scan over the DC Bias voltage range.

Bob has a ~50dB IM with two voltage pins (DC Bias and ER Tuning)


Requirements: Python3, VapScanFunc.py in same directory, packages listed below
and in VapScanFunc
OS: CentOS7

"""

from VapScanFunc import *
import pymysql
import pyvisa as visa
import socket
import time
import math
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib.pyplot as plt


#Sets directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/IntensityModulator"))


#Connect to power meter
#Need to allow permission: sudo chown inqnet4:inqnet4 /dev/usbtmc0
inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)


#Connect to mysql database
db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
					 user="<USERNAME>", #Replace <USERNAME> with your username
					 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
					 database="teleportcommission",
					 charset='utf8mb4',
					 cursorclass=pymysql.cursors.DictCursor) #name of the data



DCBias_ChannelNumber=2
DCBias_numV=20
DCBias_Vmin=10 #in Volts
DCBias_Vmax=22#in Volts
DCBias_numVScan=10
DCBias_MaxVScanRange = 0.75
DCBias_MaxVScanTime = 0.1
DCBias_MinVScanRange = 0.5
DCBias_MinVScanTime = 0.001

ERTuning_ChannelNumber=3
ERTuning_numV=10
ERTuning_Vmin=0 #in Volts
ERTuning_Vmax=6 #in Volts
ERTuning_numVScan=5
ERTuning_MaxVScanRange = 0.5
ERTuning_MaxVScanTime = 0.01
ERTuning_MinVScanRange = 0.1
ERTuning_MinVScanTime = 0.0005
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()

cur = db.cursor()
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("VapVinPIM2D.txt","w")


query = "SELECT max(id) from IM"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid=0
i = maxid +1

values = [0]*7


try:
	DCBias_Vapplied=VoltageRamp(DCBias_Vmin,DCBias_Vmax,DCBias_numV)
	ERTuning_Vapplied=VoltageRamp(ERTuning_Vmin,ERTuning_Vmax,ERTuning_numV)
	DCBias_Vin=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
	ERTuning_Vin=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
	P=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
	SetVoltage(Resource,DCBias_ChannelNumber,DCBias_Vapplied[0])
	SetVoltage(Resource,ERTuning_ChannelNumber,ERTuning_Vapplied[0])
	time.sleep(5)# Allow time for Voltage source to settle to first scan value before starting
	print('Press Ctrl-C to quit...')
	# Print nice channel column headers.
	line='  ID  |   Date/Time   |    DC Voltage Applied (V)    |    DC Voltage Measured (V)    |    ERTuning Voltage Applied (V)    |    ERTuning Voltage Measured (V)    |    Power (nW)    '.format(*range(7))
	print(line)
	if backup:
		txtFile.write(line+"\n")
	line='-' * 150
	print(line)
	if backup:
		txtFile.write(line+"\n")
	for j in range(len(ERTuning_Vapplied)): #Loop through each element in ER Tuning voltage array
		for k in range(len(DCBias_Vapplied)): #Loop through each element in DC Bias voltage array
			ERVap=ERTuning_Vapplied[j]
			DCVap=DCBias_Vapplied[k]
			values[0]=str(i)
			values[1]= str(datetime.now())
			values[2]="{0:.3f}".format(DCVap)
			values[4]="{0:.3f}".format(ERVap)
			SetVoltage(Resource,DCBias_ChannelNumber, DCVap) #Set DC Bias channel voltage of power supply
			time.sleep(0.05) #Wait
			if k == 0:
				time.sleep(2)
			DCBias_vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #DC Bias voltage reported by power supply
			DCBias_Vin[j][k]=DCBias_vMeas
			values[3]=str(DCBias_vMeas)
			SetVoltage(Resource,ERTuning_ChannelNumber, ERVap) #Set ER Tuning channel voltage of power supply
			time.sleep(0.05) #Wait
			ERTuning_vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #Channel voltage reported by power supply
			ERTuning_Vin[j][k]=ERTuning_vMeas
			values[5]=str(ERTuning_vMeas)
			p=10**9 * powermeter.read #power reported by powermeter
			P[j][k]=p
			values[6]="{0:.3f}".format(p)
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} '.format(*values)
			print(line)
			if backup:
				 txtFile.write(line+"\n")
			#SQL command to insert data into database
			query="INSERT INTO IM(datetime, DCVap, DCVin, ERVap, ERVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+","+values[5]+","+values[6]+");"
			cur.execute(query)
			db.commit()
			i+=1

	Pmin = np.amin(P) #Get min power from initial scan
	Pmax = np.amax(P)
	print(Pmin)
	PminIndex_ERTuning, PminIndex_DCBias = np.where(P==Pmin)
	print(PminIndex_ERTuning)
	print(PminIndex_DCBias)
	PminIndex_ERTuning=PminIndex_ERTuning[0] #Find ER Tuning index corresponding to min power
	PminIndex_DCBias=PminIndex_DCBias[0] #Find DC Bias index corresponding to min power
	ERTuning_Va_minP=ERTuning_Vapplied[PminIndex_ERTuning]
	DCBias_Va_minP=DCBias_Vapplied[PminIndex_DCBias]
	PmaxIndex_ERTuning, PmaxIndex_DCBias = np.where(P==Pmax)
	PmaxIndex_ERTuning=PmaxIndex_ERTuning[0]
	PmaxIndex_DCBias=PmaxIndex_DCBias[0]
	ERTuning_Va_maxP=ERTuning_Vapplied[PmaxIndex_ERTuning] #Find ER Tuning voltage corresponding to min power from init scan
	DCBias_Va_maxP=DCBias_Vapplied[PmaxIndex_DCBias] #Find DC Bias voltage corresponding to min power from init scan

	print("Pmin: ",P[PminIndex_ERTuning,PminIndex_DCBias])
	print("DC Bias Va for min P: ",DCBias_Va_minP)
	print("ER Tuning Va for min P: ",ERTuning_Va_minP)

	eRatio = -10*np.log10(Pmin/Pmax) #Max extinciton ratio from initial scan


	#Plots Power vs ER Tuning Voltage and DC Bias voltage from initial scan
	fig, axs = plt.subplots(2,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**(-6))
	PmW=np.array(PmW)
	axs[0].plot(DCBias_Vapplied,PmW[PminIndex_ERTuning,:])
	axs[0].set_xlabel("DC Bias Applied Voltage (V)")
	axs[0].set_ylabel(r"Power ($n W$)")
	axs[0].grid()
	axs[1].plot(ERTuning_Vapplied,PmW[:,PminIndex_DCBias])
	axs[1].set_xlabel("ER Tuning Applied Voltage (V)")
	axs[1].set_ylabel(r"Power ($n W$)")
	axs[1].grid()
	plt.subplots_adjust(hspace=0.4)


	#Set DC Bias voltage for min power
	SetVoltage(Resource,DCBias_ChannelNumber,DCBias_Va_minP)
	time.sleep(5) #Wait for voltage to set to Pmin
	print("DC Bias Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	#Set ER Tuning voltage for min power
	SetVoltage(Resource,ERTuning_ChannelNumber,ERTuning_Va_minP)
	time.sleep(5) #Wait for voltage to set to Pmin
	print("ER Tuning Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	time.sleep(5)
	print("P: ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime
	line='  ID  |   Date/Time   |    DC Voltage Applied (V)    |    DC Voltage Measured (V)    |    ERTuning Voltage Applied (V)    |    ERTuning Voltage Measured (V)    |    Power (nW)    '.format(*range(7))
	print(line)
	line='-' * 150
	print(line)
	n=0

	#Initial DC Bias and ER Tuning scan voltage and time ranges
	DCBias_VScanRange=DCBias_MaxVScanRange
	DCBias_VScanTime=DCBias_MaxVScanTime
	ERTuning_VScanRange=ERTuning_MaxVScanRange
	ERTuning_VScanTime=ERTuning_MaxVScanTime
	while True: #feedback loop
		curtime = datetime.now()
		SetChannel(Resource,DCBias_ChannelNumber)
		DCBias_vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #Current DC Bias voltage reported by power supply
		time.sleep(0.001)
		SetChannel(Resource,ERTuning_ChannelNumber)
		ERTuning_vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #Current ER Tuning voltage reported by powersupply
		time.sleep(0.001)
		#If at least 1 second has passed, record data:
		if (curtime-starttime) > timedelta(seconds=1):
			starttime=curtime
			values[0]=str(i)
			values[1]=str(datetime.now())
			values[2]="{0:.3f}".format(DCBias_Va_minP) #DC Bias channel voltage setpoint
			values[3] = str(DCBias_vMeas)
			values[4]="{0:.3f}".format(ERTuning_Va_minP) #ER Tuning channel voltage setpoint
			values[5] = str(ERTuning_vMeas)
			p=10**9*powermeter.read
			values[6]="{0:.3f}".format(p)
			# Print nice channel column headers.
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} '.format(*values)
			print(line)
			if backup:
				txtFile.write(line+"\n")
			#SQL command to insert data into database
			query="INSERT INTO IM(datetime, DCVap, DCVin, ERVap, ERVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+","+values[5]+","+values[6]+");"
			cur.execute(query)
			db.commit()
			i+=1
		DCBias_Vapplied = VoltageRamp(DCBias_vMeas-DCBias_VScanRange/2, DCBias_vMeas+DCBias_VScanRange/2,DCBias_numVScan) #Create fine scan DC Bias voltage array
		ERTuning_Vapplied = VoltageRamp(ERTuning_vMeas-ERTuning_VScanRange/2, ERTuning_vMeas+DCBias_VScanRange/2,ERTuning_numVScan) #Create fine scan ER Tuning voltage array
		SetVoltage(Resource,DCBias_ChannelNumber,DCBias_Vapplied[0])
		SetVoltage(Resource,ERTuning_ChannelNumber,ERTuning_Vapplied[0])
		time.sleep(0.05) #Wait to set to first element of fine scan
		DCBias_Vin=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
		ERTuning_Vin=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
		P=np.zeros((len(ERTuning_Vapplied),len(DCBias_Vapplied)))
		for j in range(len(ERTuning_Vapplied)): #Loop over elements in ER Tuning fine scan array
			for k in range(len(DCBias_Vapplied)): #Loop over elements in DC Bias fine scan array
				DCVap=DCBias_Vapplied[k]
				ERVap=ERTuning_Vapplied[j]
				SetVoltage(Resource,DCBias_ChannelNumber,DCVap)
				time.sleep(DCBias_VScanTime)
				DCBias_vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
				SetVoltage(Resource,ERTuning_ChannelNumber,ERVap)
				time.sleep(ERTuning_VScanTime)
				ERTuning_vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
				p=10**9*powermeter.read
				DCBias_Vin[j][k]=DCBias_vMeas
				ERTuning_Vin[j][k]=ERTuning_vMeas
				P[j][k]=p
		#Get min power from fine scan
		Pmin = np.amin(P)
		PminIndex_ERTuning, PminIndex_DCBias = np.where(P==Pmin)
		PminIndex_ERTuning=PminIndex_ERTuning[0]
		PminIndex_DCBias=PminIndex_DCBias[0]
		ERTuning_Va_minP=ERTuning_Vapplied[PminIndex_ERTuning] #Get ER tuning voltage corresponding to min power
		DCBias_Va_minP=DCBias_Vapplied[PminIndex_DCBias] #Get DC Bias voltage corresponding to min power

		#Calculate slope
		DCBias_dy=P[PminIndex_ERTuning,-1]-P[PminIndex_ERTuning,0]
		ERTuning_dy = P[-1,PminIndex_DCBias]-P[0,PminIndex_DCBias]
		DCBias_Slope = (P[PminIndex_ERTuning,-1]-P[PminIndex_ERTuning,0])/DCBias_VScanRange
		ERTuning_Slope = (P[-1,PminIndex_DCBias]-P[0,PminIndex_DCBias])/ERTuning_VScanRange

		#Conditionals: If slope small enough, cut the voltage and time scan ranges in half unless reach
		#the lower bound for voltage and time scan ranges
		if np.abs(DCBias_Slope) <= 400 and DCBias_VScanRange/2 > DCBias_MinVScanRange:
			DCBias_VScanRange=DCBias_VScanRange/2
			if DCBias_VScanTime/2 > DCBias_MinVScanTime:
				DCBias_VScanTime=DCBias_VScanTime/2
		if np.abs(ERTuning_Slope) <= 100 and ERTuning_VScanRange/2 > ERTuning_MinVScanRange:
			ERTuning_VScanRange=ERTuning_VScanRange/2
			if ERTuning_VScanTime/2 > ERTuning_MinVScanTime:
				ERTuning_VScanTime=ERTuning_VScanTime/2
		print(DCBias_Slope)
		print(ERTuning_Slope)
		print(DCBias_VScanRange)
		print(ERTuning_VScanRange)
		SetVoltage(Resource,DCBias_ChannelNumber,DCBias_Va_minP) #Set DC Bias voltage to optimal voltage from fine scan range
		SetVoltage(Resource,ERTuning_ChannelNumber,ERTuning_Va_minP) #Set ER Tuning voltage to optimal voltage from fine scan range
		time.sleep(1)

		#Plots of extinction ratio over time after various iterations
		if n == 100:
			fig, axs = plt.subplots(2,1,num="10")
			axs[0].plot(DCBias_Vapplied,P[PminIndex_ERTuning,:])
			axs[0].set_xlabel("DC Bias Applied Voltage (V)")
			axs[0].set_ylabel(r"Power ($n W$)")
			axs[0].grid()
			axs[1].plot(ERTuning_Vapplied,P[:,PminIndex_DCBias])
			axs[1].set_xlabel("ER Tuning Applied Voltage (V)")
			axs[1].set_ylabel(r"Power ($n W$)")
			axs[1].grid()
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan0_2D.png"
			plt.savefig(figname)
		if n == 1000:
			fig, axs = plt.subplots(2,1,num="11")
			axs[0].plot(DCBias_Vapplied,P[PminIndex_ERTuning,:])
			axs[0].set_xlabel("DC Bias Applied Voltage (V)")
			axs[0].set_ylabel(r"Power ($n W$)")
			axs[0].grid()
			axs[1].plot(ERTuning_Vapplied,P[:,PminIndex_DCBias])
			axs[1].set_xlabel("ER Tuning Applied Voltage (V)")
			axs[1].set_ylabel(r"Power ($n W$)")
			axs[1].grid()
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan1_2D.png"
			plt.savefig(figname)
		if n == 5000:
			fig, axs = plt.subplots(1,1,num="12")
			axs[0].plot(DCBias_Vapplied,P[PminIndex_ERTuning,:])
			axs[0].set_xlabel("DC Bias Applied Voltage (V)")
			axs[0].set_ylabel(r"Power ($n W$)")
			axs[0].grid()
			axs[1].plot(ERTuning_Vapplied,P[:,PminIndex_DCBias])
			axs[1].set_xlabel("ER Tuning Applied Voltage (V)")
			axs[1].set_ylabel(r"Power ($n W$)")
			axs[1].grid()
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan2_2D.png"
			plt.savefig(figname)
		n=n+1
except KeyboardInterrupt:
	print("")
	print("Quit")
if backup:
	txtFile.close()
plt.show()
db.close()
