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

if [ "$IP_ADDRESS_FILE_PATH" == "" ]; then
    export IP_ADDRESS_FILE_PATH='/home/pi/domovoi/cons_ru_ir_cn_kp_hk_tr_bg_by_sy_la_kh_th_ph_vn_mm_mn_mk_mo_af_al_rs_ba_si_hr_iq_ae_sa_ye_eg_lb_cy_pk_in_bd_bt_bh_qa_kw_kz_kg_tj_tm_uz_am_az_lk_ro_me_md.txt'
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

nohup twistd -ny ./interceptor.py > ./start_interceptor.sh.stdout.log 2> ./start_interceptor.sh.stderr.log &

popd