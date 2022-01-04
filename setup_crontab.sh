#! /bin/bash

# Note: This script is intended for unix-like systems with crontab installed
# and it has been tested only on a Raspberry Pi Zero W running the
# Raspbian distribution with PiHole running on the same machine.

if [ -d ~/domovoi ]; then
	echo "*/5 * * * * cd ~/domovoi && ./run_domain_alert.sh 2>&1 | tee ~/domovoi/run_domain_alert.sh.log" | crontab -
else
	echo "Could not find directory 'domovoi' at home directory. Please clone domovoi to your home directory."
fi

