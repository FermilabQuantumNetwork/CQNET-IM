# CQNET-IM
Code for optimizing the extinction ratio of Bob's intensity modulator.

## Overview
1. `VapScanFunc.py` (Python3, Commented, INQNET4) -- Contains functions for remotely controlling Bob's power supply.
2. `runIMFeedback1D.py` (Python3, Commented, INQNET4) -- Runs the power optimization feedback code for the DC Bias pin of Bob's intensity modulator.
3. `runIMFeedback2D.py` (Python3, Commented, INQNET4) -- Runs the power optimization feedback code for the DC Bias and ER Tuning pins of Bob's intensity modulator.
The "Other" folder contains figures, obsolete/older versions of code, etc.

## Requirements
### Mysql
The scripts here store and collect data from mysql tables from local mysql databases. If you don't have
mysql installed, you first need to install it (see https://www.mysql.com/downloads/) and create databases, tables, and users. Unless you set up the exact same databases and tables, you will probably have to change the database, table, and column names/specs in the scripts.


### Python packages
Below are listed all the packages that are used in this repo. Many may already be installed on your computer, but otherwise you should install them. Some may be redundant.
#### Python3:
* pymysql
* pyvisa
* socket
* time
* math
* ThorlabsPM100
  - USBTMC
* matplotlib
  - matplotlib.pyplot
* requests
* ast
* datetime
  - timedelta
* numpy
* getpass
* os
* subprocess
  - Popen
  - PIPE
* sys
* glob
* pipes
  - quote
* argparse

### Installation command
To install python packages, use:
* `python3 -m pip install --user <package1> <package2> ...`

### Tips
* If you are using the USBTMC driver to connect to the powermeter (via USB), you may need to first execute the terminal command: 
```sudo chown <username>:<username> /dev/<device folder>```
   - You can check for the device folder by executing `ls /dev` and unplugging/replugging in the USB into the computer.
   - The device folder names are typically named e.g. `usbtmc0` or `usbtmc1`
* For `runIMFeedback1D.py` and `runIMFeedback2D.py`, set the voltage ranges for the initial scans to be greater than Vpi to avoid power minima at the endpoints of the scan range

#### For other tips and useful commands for getting started, see the CQNET repo's README.

---
This code was written by Sam Davis at Caltech. Contact me at s1dav1s@alumni.stanford.edu if you have any questions.
