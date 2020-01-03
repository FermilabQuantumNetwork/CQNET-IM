"""
Code for plotting 2D feedback overtime for Bob's IM
"""

import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#import tkinter
#matplotlib.use('TkAgg')
import datetime
import math
import pymysql
import os


START_TIME = '2019-10-30 21:24:00'
END_TIME = '2019-10-31 09:24:00'


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


datetime_arr = []
DCBiasVap_arr=[]
DCBiasVin_arr=[]
ERTuningVap_arr=[]
ERTuningVin_arr=[]
P_arr = []

try:
	with db.cursor() as cur:
		TABLE_NAME = "IM"
		query = "SELECT datetime, DCVap, DCVin, ERVap, ERVin,P FROM "+TABLE_NAME+" WHERE datetime BETWEEN {ts %s} AND {ts %s}"
		cur.execute(query,(START_TIME,END_TIME))
		row = cur.fetchone()
		while row is not None:
			datetime_arr.append(row["datetime"])
			DCBiasVap_arr.append(row["DCVap"])
			DCBiasVin_arr.append(row["DCVin"])
			ERTuningVap_arr.append(row["ERVap"])
			ERTuningVin_arr.append(row["ERVin"])
			P_arr.append(row["P"])
			row = cur.fetchone()
finally:
	db.close()
print("len: ",len(datetime_arr))

PmW_arr=[]
for p in range(len(P_arr)):
	PmW_arr.append(10**(-6)*P_arr[p])
PmW_arr=np.array(PmW_arr)

minP=np.amin(PmW_arr)
print(minP)
maxP=np.amax(PmW_arr)
print(maxP)

eRatio= -10*np.log10(minP/maxP)
print("eRatio: ",eRatio)
firstDatetime = str(datetime_arr[0])
print(firstDatetime)
lastDatetime = str(datetime_arr[-1])
firstTime = datetime.datetime.strptime(firstDatetime,'%Y-%m-%d %H:%M:%S')
times=[]
elapsedMins=[]
elapsedHours=[]


for dt in datetime_arr:
	dt=str(dt)
	t=datetime.datetime.strptime(dt,'%Y-%m-%d %H:%M:%S')
	elapsed = t - firstTime
	times.append(t)
	elapsedMins.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes
	elapsedHours.append((elapsed.total_seconds())/3600)

elapsedMins=np.array(elapsedMins)
elapsedHours=np.array(elapsedHours)



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




#Initial Scan
DCBias_numV=20
ERTuning_numV=10
DCBiasVap_mat = np.zeros((ERTuning_numV,DCBias_numV))
DCBiasVin_mat = np.zeros((ERTuning_numV,DCBias_numV))
ERTuningVap_mat = np.zeros((ERTuning_numV,DCBias_numV))
ERTuningVin_mat = np.zeros((ERTuning_numV,DCBias_numV))
P_mat = np.zeros((ERTuning_numV,DCBias_numV))
datetime_mat=np.zeros((ERTuning_numV,DCBias_numV))

j=0
k=0
for n in range(DCBias_numV*ERTuning_numV):
	k=n%DCBias_numV
	if(k==0 and n>k):
		j=j+1
	DCBiasVap_mat[j][k]=DCBiasVap_arr[n]
	DCBiasVin_mat[j][k]=DCBiasVin_arr[n]
	ERTuningVap_mat[j][k]=ERTuningVap_arr[n]
	ERTuningVin_mat[j][k]=ERTuningVin_arr[n]
	P_mat[j][k]=PmW_arr[n]
#print(DCBiasVap_mat)
#print(ERTuningVap_mat)



Pmat_min = np.amin(P_mat)
Pmat_minIndex_ERTuning, Pmat_minIndex_DCBias = np.where(P_mat==Pmat_min)
Pmat_minIndex_ERTuning=Pmat_minIndex_ERTuning[0]
Pmat_minIndex_DCBias=Pmat_minIndex_DCBias[0]
#print(Pmat_min)


#Initial scan
fig, axs = plt.subplots(2,1, num=1)
axs[0].plot(DCBiasVap_mat[Pmat_minIndex_ERTuning,:], P_mat[Pmat_minIndex_ERTuning,:],"-bo",mfc="none")
axs[0].set_ylabel(r"Power (mW)")
axs[0].set_xlabel(r"DC $V_{ap}$ (V)")
res=fit_sin(DCBiasVap_mat[Pmat_minIndex_ERTuning,:], P_mat[Pmat_minIndex_ERTuning,:])
DCmaxP=np.abs(2*float(res["amp"]))
print(DCmaxP)
eRatio= -10*np.log10(minP/DCmaxP)
print("eRatio: ",eRatio)
fit_arr= res["fitfunc"](DCBiasVap_mat[Pmat_minIndex_ERTuning,:])
axs[0].plot(DCBiasVap_mat[Pmat_minIndex_ERTuning,:], fit_arr, "r-", label=r"P=Asin($\omega$ V + $\phi$)"+" + C \n "+"A={:.4f} mW, T={:.2f} V, ".format(np.abs(res["amp"]),res["period"])+r"$P_{min}$"+"={:.1f} nW".format(10**6 * min(fit_arr)))
axs[0].grid()
axs[0].legend()

axs[1].plot(ERTuningVap_mat[:,Pmat_minIndex_DCBias], P_mat[:,Pmat_minIndex_DCBias],"-bo",mfc="none")
axs[1].set_ylabel(r"Power (mW)")
axs[1].set_xlabel(r"ER Tuning $V_{in}$ (V)")
axs[1].grid()
res=fit_sin(ERTuningVin_mat[2:-1,Pmat_minIndex_DCBias], P_mat[2:-1,Pmat_minIndex_DCBias])
ERmaxP=np.abs(2*float(res["amp"]))
print(maxP)
eRatio= -10*np.log10(minP/ERmaxP)
print("eRatio: ",eRatio)
fit_arr= res["fitfunc"](ERTuningVap_mat[:,Pmat_minIndex_DCBias])
axs[1].plot(ERTuningVin_mat[:,Pmat_minIndex_DCBias], fit_arr, "r-", label=r"P=Asin($\omega$ V + $\phi$)"+" + C \n "+"A={:.4f} mW, T={:.2f} V, ".format(np.abs(res["amp"]),res["period"])+r"$P_{min}$"+"={:.1f} nW".format(10**6 * min(fit_arr)))#+r"$\omega$"+"={:.3e} 1/V".format(res["omega"])+"\n"+r"$\phi$"+"={:.3f} \n C={:.3e} mW".format(res["phase"],res["offset"]), linewidth=2)
fig.suptitle(r"Initial Scan")
axs[1].legend()
figname="IMOvernight2D_InitScan.png"
plt.subplots_adjust(hspace=0.4)
plt.savefig(figname)
print(figname)


best_eRatio=-10*np.log10(minP/DCmaxP)

maxP=np.amax(PmW_arr)
eRatios=[]
for p in PmW_arr:
	eRat = -10*np.log10(p/maxP)
	eRatios.append(eRat)
eRatios=np.array(eRatios)
# Pmin = np.amin(P_arr)
#
print("end of init scan: ", elapsedMins[DCBias_numV*ERTuning_numV])


#Overall Extinction
fig, axs = plt.subplots(4,1, num=20)#, sharex=True)
indices = np.where(elapsedMins>0.817)
indices = indices[0]
axs[0].plot(elapsedHours[indices[0]:indices[-1]], eRatios[indices[0]:indices[-1]])
#axs[0].set_xlim(xmin,xmax)
axs[0].set_ylabel(r"Ext. Ratio")
axs[0].grid()
axs[1].plot(elapsedHours[indices[0]:indices[-1]], P_arr[indices[0]:indices[-1]])
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()
axs[2].plot(elapsedHours[indices[0]:indices[-1]], DCBiasVap_arr[indices[0]:indices[-1]])
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC $V_{ap}$ (V)")
axs[2].grid()
axs[3].plot(elapsedHours[indices[0]:indices[-1]], ERTuningVin_arr[indices[0]:indices[-1]])
#axs[0].set_xlim(xmin,xmax)
axs[3].set_ylabel(r"ER $V_{in}$ (V)")
axs[3].grid()
axs[3].set_xlabel("Elapsed Time (Hours)")
#axs[1].set_xlim(1/60,14)
fig.suptitle(r"Best Extinction Ratio: {:.3f}".format(best_eRatio))
figname="IMOvernight2D_Overall.png"
fig.subplots_adjust(hspace=0.4)
plt.savefig(figname)
print(figname)


#Init Extinction
fig, axs = plt.subplots(4,1, num=2, sharex=True)
indices = np.where(np.logical_and(elapsedMins> 0.818, elapsedMins<12.82))
indices = indices[0]
min_eRatio = min(eRatios[indices])
max_eRatio = max(eRatios[indices])
axs[0].plot(elapsedMins[indices[0]:indices[-1]], eRatios[indices[0]:indices[-1]],"--o",mfc="none")
#axs[0].set_xlim(xmin,xmax)
axs[0].set_ylabel(r"Ext. Ratio")
axs[0].grid()
axs[1].plot(elapsedMins[indices[0]:indices[-1]], P_arr[indices[0]:indices[-1]],"--o",mfc="none")
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()
axs[2].plot(elapsedMins[indices[0]:indices[-1]], DCBiasVap_arr[indices[0]:indices[-1]],"--o",mfc="none")
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC $V_{ap}$ (V)")
axs[2].grid()
axs[3].plot(elapsedMins[indices[0]:indices[-1]], ERTuningVin_arr[indices[0]:indices[-1]],"--o",mfc="none")
#axs[0].set_xlim(xmin,xmax)
axs[3].set_ylabel(r"ER $V_{in}$ (V)")
axs[3].grid()
axs[3].set_xlabel("Elapsed Time (Mins)")
#axs[1].set_xlim(1/60,14)
fig.suptitle(r"Onset of Feedback: From {:.3f} to {:.3f} in 12 mins".format(min_eRatio,max_eRatio))
figname="IMOvernight2D_ER.png"
plt.savefig(figname)
print(figname)

#Long Term Extinction
fig, axs = plt.subplots(4,1, num=30, sharex=True)
indices = np.where(elapsedMins> 20)
indices = indices[0]
longPmax = max(PmW_arr[indices[0]:indices[-1]])
lowerbound_eRatio=-10*np.log10(longPmax/maxP)
mean_eRatio=np.mean(eRatios[indices[0]:indices[-1]])
std_eRatio=np.std(eRatios[indices[0]:indices[-1]])
axs[0].plot(elapsedHours[indices[0]:indices[-1]], eRatios[indices[0]:indices[-1]],".",mfc="none",markersize=2)
axs[0].plot(elapsedHours[indices[0]:indices[-1]],mean_eRatio*np.ones(len(eRatios[indices[0]:indices[-1]])), label=r"$\overline{ER}$="+"{:.3}dB".format(mean_eRatio)+r"$\pm$"+"{:.2f}dB".format(std_eRatio))
axs[0].set_ylabel(r"Ext. Ratio")
axs[0].grid()
axs[0].legend()
axs[1].plot(elapsedHours[indices[0]:indices[-1]], P_arr[indices[0]:indices[-1]],".",mfc="none",markersize=2)
#axs[0].set_xlim(xmin,xmax)
axs[1].set_ylabel(r"Power (nW)")
axs[1].grid()
axs[2].plot(elapsedHours[indices[0]:indices[-1]], DCBiasVap_arr[indices[0]:indices[-1]],".",mfc="none",markersize=2)
#axs[0].set_xlim(xmin,xmax)
axs[2].set_ylabel(r"DC $V_{ap}$ (V)")
axs[2].grid()
axs[3].plot(elapsedHours[indices[0]:indices[-1]], ERTuningVin_arr[indices[0]:indices[-1]],".",mfc="none",markersize=2)
#axs[0].set_xlim(xmin,xmax)
axs[3].set_ylabel(r"ER $V_{in}$ (V)")
axs[3].grid()
axs[3].set_xlabel("Elapsed Time (Hours)")
fig.suptitle(r"Extinction Ratio $\geq$ {:.4} for {:.2f} hours".format(lowerbound_eRatio, elapsedHours[indices[-1]]-elapsedHours[indices[0]]))
figname="IMOvernight2D_ER_Long.png"
plt.savefig(figname)
print(figname)
