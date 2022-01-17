#! /bin/bash


# Don't restart if we don't need it.
if [ "$(ps -ef | grep 'twistd -ny interceptor.py' | grep -v 'grep')" != "" ]; then
    exit 0
fi

pushd ~/domovoi

echo "Activating virtualenv."
if [ -f ".env/Scripts/activate" ]; then
	source .env/Scripts/activate;
elif [ -f ".env/bin/activate" ]; then
	source .env/bin/activate;
else
	echo "No environment activation found. Please try again.";
	exit 3;
fi

export PYTHONPATH=$PYTHONPATH:.

if [ "$IP_ADDRESS_FILE_PATH" == "" ]; then
    export IP_ADDRESS_FILE_PATH='cons_ru_ir_cn_kp_hk_tr_bg_by_sy_la_kh_th_ph_vn_mm_mn_mk_mo_af_al_rs_ba_si_hr_iq_ae_sa_ye_eg_lb_cy_pk_in_bd_bt_bh_qa_kw_kz_kg_tj_tm_uz_am_az_lk_ro_me_md.txt'
fi

cd 

nohup twistd -ny interceptor.py > /home/pi/domovoi/start_interceptor.sh.stdout.log 2> /home/pi/domovoi/start_interceptor.sh.stderr.log &
