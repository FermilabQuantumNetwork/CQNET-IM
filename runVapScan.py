from VapScanFunc import *
import pymysql
import pyvisa as visa
import socket
import time
import math
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib.pyplot as plt
import matplotlib as mpl
#Need to allow permission: sudo chown inqnet4:inqnet4 /dev/usbtmc0

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/IntensityModulator"))





db = pymysql.connect(host = "192.168.0.125", #Wired IPv4 Address
					user ="INQNET4", # this user only has access to CP
					password="Teleport1536!", # your password
					database="teleportcommission",
					charset='utf8mb4',
					#port = 5025,
					cursorclass=pymysql.cursors.DictCursor) #name of the data




#inst = USBTMC(device="/dev/usbtmc1")
#powermeter = ThorlabsPM100(inst=inst)
VISAInstance=pyvisa.ResourceManager('@py')
resourceName='USB0::4883::32888::P0023460::0::INSTR'
inst=VISAInstance.open_resource(resourceName)
print(inst.ask("*IDN?"))
powermeter = ThorlabsPM100(inst=inst)
#ChannelNumber=2
numV=400
Vmin=0 #in Volts
Vmax=22#in Volts
Vscan = 0.05
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()


channelNum = 2
ChannelNumber=int(channelNum)



cur = db.cursor()
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("VapVinPIM.txt","w")


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
	Vapplied=VoltageRamp(Vmin,Vmax,numV)
	t=np.arange(1,1+len(Vapplied))
	Vin=[]
	P=[]
	Va=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |   Date/Time   |    Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	if backup:
		txtFile.write(line+"\n")
	line='-' * 100
	print(line)
	#print(Vapplied[0])
	SetVoltage(Resource,ChannelNumber,Vapplied[0])
	time.sleep(5)
	if backup:
		txtFile.write(line+"\n")
	for Vap in Vapplied:
		values[0]=str(i)
		values[1]= str(datetime.now())
		values[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,ChannelNumber,Vap)
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		Vin.append(vMeas)
		values[3]=str(vMeas)
		p=10**9*powermeter.read
		P.append(p)
		values[4]="{0:.3f}".format(p)
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
		print(line)
		if backup:
		     txtFile.write(line+"\n")
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
		cur.execute(query)
		db.commit()
		i+=1
	Vin = np.array(Vin)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Exinction Ratio Lower Bound: ", eRatio)

	#Initial scan
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(Vapplied,PmW, label = "Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")
	figname="InitScan.png"
	#plt.savefig(figname)


	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=Vapplied[PminIndex[0]]
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=Vapplied[PmaxIndex[0]]
	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)
	SetVoltage(Resource,ChannelNumber,Va_minP)
	time.sleep(10)
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime
	#Ptot=[]
	#Vatot=[]
	#Vintot=[]
	line='  ID  |   Date/Time   |    Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	line='-' * 100
	print(line)
	n=0
	while True:#for n in range(3):#while True:
		curtime = datetime.now()
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		if (curtime-starttime) > timedelta(seconds=1):
			starttime=curtime
			values[0]=str(i)
			values[1]=str(datetime.now())
			values[2]="{0:.3f}".format(Va_minP)
			values[3] = str(vMeas)
			p=10**9 * powermeter.read
			values[4]="{0:.3f}".format(p)
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
			print(line)
			if backup:
				txtFile.write(line+"\n")
			query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
			cur.execute(query)
			db.commit()
			i+=1
		P=[]
		Vin=[]
		Vapplied = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,ChannelNumber,Vapplied[0])
		time.sleep(0.1)
		for Vap in Vapplied:
			#if Vap > 20 or Vap < 0:
			#	time.sleep()
			#	if Vap < 0:
			#		Vap = 20 + Vap
			#Vap = np.mod(Vap,20)
			SetVoltage(Resource,ChannelNumber,Vap)
			#time.sleep(0.05)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			Vin.append(vMeas)
			p=0
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		Vin=np.array(Vin)
		Pmin = np.amin(P)
		#print(Pmin)
		PminIndex = np.where(P==Pmin)
		PminIndex=PminIndex[0]
		#print(PminIndex[0])
		Va_minP=Vapplied[PminIndex[0]]
		#Ptot.append(P)
		#Vintot.append(Vin)
		#Vatot.append(Vapplied)
		#print(P)
		#print(Pmin)
		SetVoltage(Resource,ChannelNumber,Va_minP)
		if n == 1:
			fig, axs = plt.subplots(1,1,num="10")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan0.png"
			#plt.savefig(figname)
		if n == 5:
			fig, axs = plt.subplots(1,1,num="11")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan1.png"
			#plt.savefig(figname)
		if n == 10:
			fig, axs = plt.subplots(1,1,num="12")
			axs.plot(Vapplied,P)
			axs.grid()
			axs.set_xlabel("Applied Voltage (V)")
			axs.set_ylabel(r"Power ($n W$)")
			plt.subplots_adjust(hspace=0.4)
			figname="FineScan2.png"
			#plt.savefig(figname)
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
