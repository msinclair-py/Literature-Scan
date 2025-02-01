#! /bin/bash

TARGETS=$1
for n in `cat ${TARGETS}` ; do
    mkdir $n ; 
    python -u ./ls_main2.py --term $n --logfile $n/log --get_partners --no_delete > $n/out
done
