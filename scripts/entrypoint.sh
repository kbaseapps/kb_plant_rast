#!/bin/bash

. /kb/deployment/user-env.sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "init" ] ; then
  echo "Init module"
  cd /data
  PLANTSEED_KMER_FILE="https://raw.githubusercontent.com/ModelSEED/PlantSEED/master/Data/PlantSEED_v2/Flat_Files/Supporting_Data_S3_Signature_Kmers.txt"
  curl -s $PLANTSEED_KMER_FILE > functions_kmers.txt
  if [ -f functions_kmers.txt ] ; then
    touch __READY__
    echo "Init succeeded"
  else
    echo "Init failed"
  fi
elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  make compile
else
  echo Unknown
fi
