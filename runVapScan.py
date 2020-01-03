"""
This script maximizes Bob's IM extinction ratio by minimizing the IM's output
optical power and prevents drifting.
It scans over the DC Bias voltage for Bob's intensity modulator (IM) and
finds the tuning voltage corresponding to the minimum output power, then
periodically does fine range scans to find and keep the IM at min power.

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
import matplotlib as mpl

#Sets directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/IntensityModulator"))


#Connect to mysql database
db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
					 user="<USERNAME>", #Replace <USERNAME> with your username
					 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
					 database="teleportcommission",
					 charset='utf8mb4',
					 cursorclass=pymysql.cursors.DictCursor)




#Connect to powermeter
VISAInstance=pyvisa.ResourceManager('@py')
resourceName='USB0::4883::32888::P0023460::0::INSTR'
inst=VISAInstance.open_resource(resourceName)
print(inst.ask("*IDN?"))
powermeter = ThorlabsPM100(inst=inst)

Vscan = 0.05 #Range of fine scan (V)
numV=400 #Number of points to divide initial scan range for IM
Vmin=0 #in Volts
Vmax=22#in Volts

#Connect to powersupply
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()

#Channel number corresponding to Bob's DC Bias pin
channelNum = 2
ChannelNumber=int(channelNum)


#Create cursor to select data from mysql.
cur = db.cursor()
#Option to back up data to textfile
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("VapVinPIM.txt","w")


#Mysql commands to get the index of the last entry of IM table
query = "SELECT max(id) from IM"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid=0
i = maxid +1


try:
	values = [0]*5
	Vapplied=VoltageRamp(Vmin,Vmax,numV) #Returns array of Vap elements for initial scan of IM algorithm
	t=np.arange(1,1+len(Vapplied))
	Vin=[]
	P=[]
	Va=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	# Print nice channel column headers.
	line='  ID  |   Date/Time   |    Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	if backup:
		txtFile.write(line+"\n")
	line='-' * 100
	print(line)
	SetVoltage(Resource,ChannelNumber,Vapplied[0])
	time.sleep(5) #Give time to settle to first voltage of Vapplied array
	if backup:
		txtFile.write(line+"\n")
	for Vap in Vapplied: #Loops through elements in Vapplied array for initial scan, sets power supply to each element.
		values[0]=str(i)
		values[1]= str(datetime.now())
		values[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,ChannelNumber,Vap) #Set channel voltage of power supply
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())  #Channel voltage reported by power supply
		Vin.append(vMeas)
		values[3]=str(vMeas)
		p=10**9*powermeter.read #power reported by power meter
		P.append(p)
		values[4]="{0:.3f}".format(p)
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
		print(line)
		if backup:
			 txtFile.write(line+"\n")
		#SQL command to insert data into database
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
		cur.execute(query)
		db.commit()
		i+=1
	Vin = np.array(Vin)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Exinction Ratio Lower Bound: ", eRatio) #Max extinction ratio (ER) from initial scan

	#Plots Power vs Applied Voltage from initial scan
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(Vapplied,PmW, label = "Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")



	#Get index corresponding to min of power from init scan
	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=Vapplied[PminIndex[0]] #Find voltage value corresponding to min power

	#Get index corresponding to max of power from init scan
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=Vapplied[PmaxIndex[0]] #Find voltage value corresponding to max power

	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)

	#Set powersupply voltage to min power
	SetVoltage(Resource,ChannelNumber,Va_minP)
	time.sleep(10) #Wait to settle at the max voltage
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime
	line='  ID  |   Date/Time   |    Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	line='-' * 100
	print(line)
	n=0
	while True: #feedback loop
		curtime = datetime.now()
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		#if at least one second has passed, record data:
		if (curtime-starttime) > timedelta(seconds=1):
			starttime=curtime
			values[0]=str(i)
			values[1]=str(datetime.now())
			values[2]="{0:.3f}".format(Va_minP) #Voltage channel setpoint
			values[3] = str(vMeas) #Channel voltage as reported by power supply
			p=10**9 * powermeter.read #Measure power from powermeter
			values[4]="{0:.3f}".format(p)
			# Print nice channel column headers.
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
			print(line)
			if backup:
				txtFile.write(line+"\n")
			#SQL command to insert data into database
			query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
			cur.execute(query)
			db.commit()
			i+=1
		P=[] #Array for power measurements from fine scan
		Vin=[] #Array for channel voltage measurements from fine scan
		Vapplied = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40) #See VapScanFunc.py
		SetVoltage(Resource,ChannelNumber,Vapplied[0])
		time.sleep(0.1)
		#Loops through elements in fine scan Vapplied array, sets power supply to each element.
		for Vap in Vapplied:
			SetVoltage(Resource,ChannelNumber,Vap)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			Vin.append(vMeas)
			p=0
			#Gets average of 10 powermeter measurements in rapid succession
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		Vin=np.array(Vin)
		Pmin = np.amin(P) #Get min power from fine scan
		PminIndex = np.where(P==Pmin) #Get index of min power from fine scan
		PminIndex=PminIndex[0]
		Va_minP=Vapplied[PminIndex[0]] #Get voltage corresponding to min power from fine scan
		SetVoltage(Resource,ChannelNumber,Va_minP) #Set to voltage of min power from previous scan

		#Plots of extinction ratio over time after various iterations
		if n == 1:
			fig, axs = plt.subplots(1,1,num="10")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan0.png"
		if n == 5:
			fig, axs = plt.subplots(1,1,num="11")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan1.png"
		if n == 10:
			fig, axs = plt.subplots(1,1,num="12")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan2.png"
		n=n+1
		time.sleep(3)
except KeyboardInterrupt:
	print("")
	print("Quit")
	DisableLVOutput(inst)
if backup:
	txtFile.close()
plt.show()
db.close()
