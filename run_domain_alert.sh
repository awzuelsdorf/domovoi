#! /bin/bash

if [ "$(/usr/bin/which virtualenv)" == "" ]; then
        echo "No virtualenv command found. Please install virtualenv and try again.";
        exit 1;
fi

if [ ! -d ".env" ]; then
        echo "No virtualenv .env found. Creating one.";

        if [ "$(/usr/bin/which python3)" != "" ]; then
                virtualenv -p python3 .env;
        else
                virtualenv .env;
        fi

        echo "Activating virtualenv.";

        if [ -f ".env/Scripts/activate" ]; then
                source .env/Scripts/activate;
        elif [ -f ".env/bin/activate" ]; then
                source .env/bin/activate;
        else
                echo "No environment activation found. Please try again.";
                exit 2;
        fi

        echo "Installing requirements to virtualenv.";
        pip install -r requirements.txt;

        echo "Finished creating virtualenv";
        deactivate;
fi

echo "Activating virtualenv."
if [ -f ".env/Scripts/activate" ]; then
        source .env/Scripts/activate;
elif [ -f ".env/bin/activate" ]; then
        source .env/bin/activate;
else
        echo "No environment activation found. Please try again.";
        exit 3;
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

if [ "$PI_HOLE_PW" == "" ]; then
        echo "No PI_HOLE_PW environment variable defined. Please try again."
        exit 9
fi

if [ "$PI_HOLE_URL" == "" ]; then
        echo "No PI_HOLE_URL environment variable defined. Please try again."
        exit 10
fi

python new_domain_alert.py 2>&1 | tee run_domain_alert.sh.log;

