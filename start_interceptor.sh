#! /bin/bash

# Don't restart if we don't need it.
if [ "$(ps -ef | grep 'twistd -ny ' | grep 'interceptor.py' | grep -v 'grep')" != "" ]; then
    exit 0
fi

pushd /home/pi/domovoi

echo "Activating virtualenv."
if [ -f ".env/Scripts/activate" ]; then
        source .env/Scripts/activate;
elif [ -f ".env/bin/activate" ]; then
        source .env/bin/activate;
else
        echo "No environment activation found. Please try again.";
        exit 3;
fi

export PYTHONPATH=$PYTHONPATH:/home/pi/domovoi:.

if [ "$INTERCEPTOR_PORT" == "" ]; then
        export INTERCEPTOR_PORT='47786'
fi

if [ "$INTERCEPTOR_UPSTREAM_DNS_SERVER_IP" == "" ]; then
        export INTERCEPTOR_UPSTREAM_DNS_SERVER_IP='1.1.1.1'
fi

if [ "$INTERCEPTOR_UPSTREAM_DNS_SERVER_PORT" == "" ]; then
        export INTERCEPTOR_UPSTREAM_DNS_SERVER_PORT='53'
fi

if [ "$IP2LOCATION_BIN_FILE_PATH" == "" ]; then
        export IP2LOCATION_BIN_FILE_PATH='IP2LOCATION-LITE-DB1.BIN'
fi

if [ "$IP2LOCATION_MODE" == "" ]; then
        export IP2LOCATION_MODE='SHARED_MEMORY'
fi

if [ "$BLOCKED_COUNTRIES_LIST" == "" ]; then
        export BLOCKED_COUNTRIES_LIST="ru,ir,cn,kp,hk,tr,bg,by,sy,la,kh,th,ph,vn,mm,mn,mk,mo,af,al,rs,ba,si,hr,iq,ae,sa,ye,eg,lb,cy,pk,in,bd,bt,bh,qa,kw,kz,kg,tj,tm,uz,am,az,lk,ro,me,md,cu,il,sk,br"
fi

if [ ! -f ".twilio_creds" ]; then
        echo "No .twilio_creds file found. Please try again."
        exit 4
fi

source ./.twilio_creds;

if [ "$TWILIO_PHONE" == "" ]; then
        echo "No TWILIO_PHONE environment variable defined. Please try again."
        exit 5
fi

if [ "$TWILIO_ACCOUNT_SID" == "" ]; then
    echo "No TWILIO_ACCOUNT_SID environment variable defined. Please try again."
        exit 6
fi

if [ "$TWILIO_AUTH_TOKEN" == "" ]; then
        echo "No TWILIO_AUTH_TOKEN environment variable defined. Please try again."
        exit 7
fi

if [ "$ADMIN_PHONE" == "" ]; then
        echo "No ADMIN_PHONE environment variable defined. Please try again."
        exit 8
fi

if [ -f "./twistd.pid" ]; then
        /bin/rm -f ./twistd.pid
fi

nohup twistd -ny ./interceptor.py > ./start_interceptor.sh.stdout.log 2> ./start_interceptor.sh.stderr.log &

popd
