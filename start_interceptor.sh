#! /bin/bash

source .env/bin/activate

export IP_ADDRESS_FILE_PATH='cons_ru_ir_cn_kp_hk_tr_bg_by_sy_la_kh_th_ph_vn_mm_mn_mk_mo_af_al_rs_ba_si_hr_iq_ae_sa_ye_eg_lb_cy_pk_in_bd_bt_bh_qa_kw.txt'

nohup twistd -ny interceptor.py > /home/pi/domovoi/start_interceptor.sh.stdout.log 2> /home/pi/domovoi/start_interceptor.sh.stderr.log &
