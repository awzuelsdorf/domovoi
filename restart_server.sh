#! /bin/bash

if [ "$(ps -ef | grep runserver | grep -v grep)" == "" ]; then
	push /home/pi/domovoi

	source .env/bin/activate

	cd ui

	nohup python manage.py runserver 192.168.0.102:8010 &

	popd
fi
