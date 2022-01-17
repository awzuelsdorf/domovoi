#! /bin/bash

# Note: This script is intended for unix-like systems with crontab installed
# and it has been tested only on a Raspberry Pi Zero W running the
# Raspbian distribution with PiHole running on the same machine.

if [ -d ~/domovoi ]; then
        cd ~/domovoi && chmod +x ./run_domain_alert.sh && ./run_domain_alert.sh 2>&1 | tee ~/domovoi/run_domain_alert.sh.log
        (crontab -l ; echo "*/5 * * * * cd ~/domovoi && ./run_domain_alert.sh 2>&1 | tee ~/domovoi/run_domain_alert.sh.log") | crontab -
        (crontab -l ; echo "*/1 * * * * cd ~/domovoi && sudo ./start_interceptor.sh") | crontab -
else
        echo "Could not find directory 'domovoi' at home directory. Please clone domovoi to your home directory."
fi
