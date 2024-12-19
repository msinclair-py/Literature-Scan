#! /bin/bash

TARGETS=$1
for n in `cat ${TARGETS}` ; do
    mkdir $n ; 
    /opt/miniconda3/envs/litscan/bin/python -u /Users/brettin/github/Literature-Scan/relevancy/ls_main2.py --term $n --logfile $n/log --get_partners > $n/out
done
