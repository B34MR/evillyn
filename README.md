![Supported Python versions](https://img.shields.io/badge/python-3.10-green.svg)

# Evil-Lyn
An EvilTwin wrapper with quality of life enhancements.
<br>

**Developed and Tested on:**
```
Kali-Linux
```

**Installation:**
```
At this time standard installation only requires the Python3 'rich' library.
python3 -m pip install -r requirements.txt
or
python3 -m pip install rich
```

**Usage:**
```
Usage Examples: 
  python evillyn.py -i wlan0 -e 'Contoso' -m AA:AA:AA:FF:FF:FF -c 4 --company 'Contoso, Ltd.' --band b
 
```

**Options:**
```
Interface Arguments:
  -i                   Set interface [wlan0]
  -m                   Set interface MAC [FF:FF:FF:00:00:00]
  --reg                Set inteface Regulatory Domain [US]
  --txpower            Set interface TX Power [30]

Hostapd Arguments:
  -c                   Set Hostapd Channel [4]
  -e                   Set Hostapd ESSID [Contoso, Ltd.]
  --band {A, B, G}     Set Hostpad wireless band [B]
  --cc                 Set Hostapd Country Code [US]

OpenSSL Arguments:
  --country            Set certificate Country [US]
  --state              Set certificate State [CA]
  --city               Set certificate City [San Diego]
  --company            Set certificate Company Name [Contoso]
  --ou                 Set certificate Organizational Unit (OU) [Contoso, Ltd.]
  --email              Set certificate Email [info@contoso.com]

Global Arguments:
  --database DATABASE  Specifty database filepath [.evillyn.db]
  --droptables         Drop all database tables
  --debug              Set logging level [DEBUG]
  --minimal            Disable DBmanager and Prettify mode
  --runtime RUNTIME    Set Runtime duration in seconds
```

**Database:**
```
Evil-Lyn uses a SQLite3 database to store captured user identities and hashes.
The identities and hashes are then called from the database and written to a flat file per use.
Results are stored in the 'results' directory using the '[ESSID].hc, [ESSID].id and [ESSID].log' naming convention.
```

**DBmanager:**
```
The DBmanager will check if the SQLite3 database has any existing entries from previous EvilTwin attacks on launch.
If existing entries are found the following notification will appear and allows you to proceed and merge data sets \
or drop the existing table(s) for a fresh start.
Optionaly, a new Database Workspace can be created. (See below)

Existing entries were found in the database.
Continuing will merge the new and existing data.
Select the (M)enu option to drop specific db tables.

        Database Tables
+-----------------------------+
| Table Name | Number of Rows |
|------------+----------------|
| Identity   | [6]            |
| NetNTLM    | [1]            |
+-----------------------------+
0. All Tables
1. Identity
2. NetNTLM
3. Quit
Select table to drop: 0
 
```

**Database Workspaces:**
```
The default database workspace is '.evillyn.db' and automatically selected upon launch.
Create and use custom database workspace with the '--database' argument.
Using a custom database workspace requires the '--database' argument to be called on each use.  

Usage Examples: 
  python evillyn.py -i wlan0 -e 'Contoso' -m AA:AA:AA:FF:FF:FF -c 4 --company 'Contoso, Ltd.' --band b --database workspace1.db
 
```

**Minimal Installation:**
```
Minimal installation only uses modules from the Python Standard Library, no additional dependencies are required.
Note, the minimal installation cannot use DBmanager and Prettify as these require the Python3 'rich' Library.
```

**Minimal Mode:**
```
Minimal mode will disable DBmanager and Prettify, resulting in a basic 'look' to the text printed to standard out.
This can be useful at times when installation of additional Python Libraries is not possible.

Usage Examples: 
  python evillyn.py -i wlan0 -e 'Contoso' -m AA:AA:AA:FF:FF:FF -c 4 --company 'Contoso, Ltd.' --band b --minimal
 
```

**Troubleshooting:**
```
ISSUE:
  wlan0: AP-ENABLED
  wlan0: INTERFACE-DISABLED
  wlan0: INTERFACE-ENABLED

SOLUTION:
  Configure NetworkManager to stop 'managing' your wireless interface. 
  nmcli device set wlan0 managed no
```