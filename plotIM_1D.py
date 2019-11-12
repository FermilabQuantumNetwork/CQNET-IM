#!/usr/bin/python2.7

import numpy as np
#import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.optimize
#import tkinter
#matplotlib.use('TkAgg')
import datetime
import math
import pymysql
import os


START_TIME = '2019-10-29 18:52:00'
END_TIME = '2019-10-30 08:52:00'



#connect to database

db = pymysql.connect(host="192.168.0.125",  # this PC
                     user="inqnet1",
                     passwd="Teleport1536!",  # your password
                     db="teleportcommission",
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)
        #auth_plugin='mysql_native_password')        # name of the data base

# you must create a Cursor object. It will let
#  you execute all the queries you need


datetimes = []
DCVap=[]
DCVin=[]
P = []

try:
    with db.cursor() as cur:
        TABLE_NAME = "IM"
        query = "SELECT datetime, DCVap, DCVin,P FROM "+TABLE_NAME+" WHERE datetime BETWEEN {ts %s} AND {ts %s}"
        cur.execute(query,(START_TIME,END_TIME))
        row = cur.fetchone()
        while row is not None:
            datetimes.append(row["datetime"])
            DCVap.append(row["DCVap"])
            DCVin.append(row["DCVin"])
            P.append(row["P"])
            row = cur.fetchone()
finally:
    db.close()

Pmin = min(P)
Pmax=max(P)

eRatios=[]
for p in P:
    e = -10*np.log10(p/Pmax)
    eRatios.append(e)
eRatios=np.array(eRatios)



firstDatetime = str(datetimes[0])
print(firstDatetime)
lastDatetime = str(datetimes[-1])
firstTime = datetime.datetime.strptime(firstDatetime,'%Y-%m-%d %H:%M:%S')
times=[]
elapsedMins=[]
elapsedHours=[]

for dt in datetimes:
    dt=str(dt)
    t=datetime.datetime.strptime(dt,'%Y-%m-%d %H:%M:%S')
    elapsed = t - firstTime
    times.append(t)
    elapsedMins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
    elapsedHours.append((elapsed.total_seconds())/3600) #Convert elapsed time from seconds to minutes

datetimes = np.array(datetimes)
elapsedMins=np.array(elapsedMins)
elapsedHours=np.array(elapsedHours)
DCVap=np.array(DCVap)
DCVin=np.array(DCVin)
P=np.array(P)


#Fit to sine curve
def fit_sin(tt, yy):
	'''Fit sin to the input time sequence, and return fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc"'''
	tt = np.array(tt)
	yy = np.array(yy)
	ff = np.fft.fftfreq(len(tt), (tt[1]-tt[0]))   # assume uniform spacing
	Fyy = abs(np.fft.fft(yy))
	guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   # excluding the zero frequency "peak", which is related to offset
	guess_amp = np.std(yy) * 2.**0.5
	guess_offset = np.mean(yy)
	guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

	def sinfunc(t, A, w, p, c):  return A * np.sin(w*t + p) + c
	popt, pcov = scipy.optimize.curve_fit(sinfunc, tt, yy, p0=guess)
	A, w, p, c = popt
	f = w/(2.*np.pi)
	fitfunc = lambda t: A * np.sin(w*t + p) + c
	return {"amp": A, "omega": w, "phase": p, "offset": c, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}



#Initial scan
fig, axs = plt.subplots(1,1, num=1, sharex=True)
indices = np.where(elapsedMins <0.5)
indices = indices[0]
Pm=[]
for k in range(len(P)):
    Pm.append(10**(-6)*P[k])
Pm=np.array(Pm)
axs.plot(DCVap[indices], Pm[indices],"-bo",mfc="none",markersize=3)
res=fit_sin(DCVap[indices], Pm[indices])
DCmaxP=np.abs(2*float(res["amp"]))
print(DCmaxP)
eRatio= -10*np.log10(Pmin/DCmaxP)
print("eRatio: ",eRatio)
fit_arr= res["fitfunc"](DCVap[indices])
axs.plot(DCVap[indices], fit_arr, "r-", label=r"P=Asin($\omega$ V + $\phi$)"+" + C \n "+"A={:.3f} mW, T={:.1f} V, ".format(np.abs(res["amp"]),res["period"])+r"$P_{min}$"+"={:.1f} nW".format(10**6 * min(fit_arr)))
axs.set_ylabel(r"Power (mW)")
axs.set_xlabel(r"DC Applied Voltage (V)")
axs.grid()
fig.suptitle(r"Initial Scan")
axs.legend()
figname="IMOvernight1D_InitScan.png"
plt.savefig(figname)
print(figname)


best_eRatio=-10*np.log10(Pmin/(DCmaxP*10**6))
print("Best Extinction Ratio: ", best_eRatio)

#Overall Extinction
fig, axs = plt.subplots(3,1, num=20, sharex=True)
indices = np.where(elapsedMins>0.6)
indices = indices[0]
axs[0].plot(elapsedHours[indices], eRatios[indices])
#axs[0].set_xlim(xmin,xmax)
axs[0].set_ylabel(r"Extinction Ratio")
axs[0].grid()


axs[1].plot(elapsedHours[indices], P[indices])
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()


axs[2].plot(elapsedHours[indices], DCVap[indices])
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC Applied Voltage (V)")
axs[2].grid()
axs[2].set_xlabel("Elapsed Time (Hours)")
#axs[1].set_xlim(1/60,14)
fig.suptitle(r"Best Extinction Ratio: {:.3f}".format(best_eRatio))
figname="IMOvernight1D_Overall.png"
plt.savefig(figname)
print(figname)


#Init Extinction
fig, axs = plt.subplots(3,1, num=2, sharex=True)
indices = np.where(np.logical_and(elapsedMins>0.5, elapsedMins<12.5))
indices = indices[0]
min_eRatio = min(eRatios[indices])
max_eRatio = max(eRatios[indices])

axs[0].plot(elapsedMins[indices], eRatios[indices],"--.",mfc="none")#,markersize=)
#axs[0].set_xlim(xmin,xmax)
axs[0].set_ylabel(r"Extinction Ratio")
axs[0].grid()

axs[1].plot(elapsedMins[indices], P[indices],"--.",mfc="none")#,markersize=2)
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()

axs[2].plot(elapsedMins[indices], DCVap[indices],"--.",mfc="none")#,markersize=2)
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC Applied Voltage (V)")
axs[2].grid()
axs[2].set_xlabel("Elapsed Time (Min)")
#axs[1].set_xlim(1/60,14)
fig.suptitle(r"Onset of Feedback: From {:.3f} to {:.3f} in 12 mins".format(min_eRatio,max_eRatio))
figname="IMOvernight1D_ER.png"
plt.savefig(figname)
print(figname)

#Long Term Extinction
fig, axs = plt.subplots(3,1, num=3, sharex=True)
indices = np.where(elapsedMins>20)
indices = indices[0]

longPmax = max(P[indices])
lowerbound_eRatio=-10*np.log10(longPmax/Pmax)
mean_eRatio=np.mean(eRatios[indices])
std_eRatio=np.std(eRatios[indices])

axs[0].plot(elapsedHours[indices], eRatios[indices], linestyle = 'none', marker = '.', markersize = 2)
#axs[0].set_xlim(xmin,xmax)
axs[0].plot(elapsedHours[indices],mean_eRatio*np.ones(len(indices)), label=r"$\overline{ER}$="+"{:.3}".format(mean_eRatio)+r"$\pm$"+"{:.2f}dB".format(std_eRatio))
axs[0].set_ylabel(r"Extinction Ratio")
axs[0].legend()
axs[0].grid()

axs[1].plot(elapsedHours[indices], P[indices],  linestyle = 'none', marker = '.', markersize = 2)
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()

axs[2].plot(elapsedHours[indices], DCVap[indices],  linestyle = 'none', marker = '.', markersize = 2)
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC Applied Voltage (V)")
axs[2].grid()
axs[2].set_xlabel("Elapsed Time (Hours)")

fig.suptitle(r"Extinction Ratio $\geq$ {:.4} for {:.2f} hours".format(lowerbound_eRatio, elapsedHours[indices[-1]]-elapsedHours[indices[0]]))
figname="IMOvernight1D_ER_Long.png"
plt.savefig(figname)
print(figname)
