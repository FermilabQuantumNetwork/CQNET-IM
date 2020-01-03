import socket
import time
import math
import pymysql

import pyvisa as visa
from ThorlabsPM100 import ThorlabsPM100, USBTMC
#Need to allow permission: sudo chown inqnet4:inqnet4 /dev/usbtmc0


db = pymysql.connect(host = "192.168.0.125", #Wired IPv4 Address
							 user ="INQNET4", # this user only has access to CP
							 password="Teleport1536!", # your password
							 database="teleportcommission",
							 charset='utf8mb4',
							 #port = 5025,
							 cursorclass=pymysql.cursors.DictCursor) #name of the data


inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)

cur = db.cursor()
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("PInterfStable.txt","w")

#Get max id
query = "SELECT max(id) from Power"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid = 0
i = maxid +1



print('Reading Powermeter values, press Ctrl-C to quit...')
# Print nice channel column headers.
line='  ID  |   Date/Time   |    Power   '.format(*range(3))
print(line)
if backup:
	txtFile.write(line+"\n")
line='-' * 50
print(line)
if backup:
	txtFile.write(line+"\n")
values = [0]*3


while True:
	try:
		values[0]=str(i)
		values[1] = str(time.ctime())
		p=powermeter.read
		values[2] = str(p)
		line = ' {0:>6} | {1:>6} |  {2:>6} '.format(*values)
		print(line)
		if(backup):
			txtFile.write(line+"\n")
		query="INSERT INTO Power(P, datetimeP) values("+values[2]+", NOW());"
		cur.execute(query)
		db.commit()
		time.sleep(1)
		i+=1
	except KeyboardInterrupt:
		print("")
		print("quit")
		break
if backup:
	txtFile.close()
db.close()
