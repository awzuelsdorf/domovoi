#! /bin/bash

source .env/bin/activate

nohup twistd -ny interceptor.py > /home/pi/domovoi/start_interceptor.sh.stdout.log 2> /home/pi/domovoi/start_interceptor.sh.stderr.log &
