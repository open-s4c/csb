#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


if [ $# -ne 2 ]; then
  echo "Usage: $0 <strace.log> </path/to/prog/dir>"
  exit 1
fi

# calculates the precentage like 100*$2/$1 with $3 number of digits (2 if $3 is empty)
calc_percent() {
  a=$1
  b=$2
  digits=$3
  if [ "x${digits}" == "x" ]; then
    digits=2
  fi
  echo "scale=${digits}; 100*${b}/${a}" | bc -l
}

TRACE="$1"
DIR_PROG="$2"

FILE_FREQ_IN="${DIR_PROG}/frequency_in.log"
FILE_FREQ_OUT="${DIR_PROG}/frequency_out.log"

FILE_NAMES_IN="${DIR_PROG}/syscall_names_in.log"
FILE_NAMES_OUT="${DIR_PROG}/syscall_names_out.log"

# Generate strace log input frequencies

cat "${TRACE}" | grep -vF '<...' | grep -vF -- '---' | grep -vF -- '+++' | sed 's/ \+/ /'  | cut -d ' ' -f 2 | cut -d '(' -f 1 | sort | uniq -c | sed 's/^ *//' | sed 's/^\(.*\) \(.*\)$/\2\t\1/' > "${FILE_FREQ_IN}"

# Generate prog output frequencies

cat "${DIR_PROG}/"*.prog | sed 's/^<[0-9]*>r.* = //' | cut -d '(' -f 1 | cut -d '$' -f 1 | sort | uniq -c | sed 's/^ *//' | sed 's/^\(.*\) \(.*\)$/\2\t\1/' > "${FILE_FREQ_OUT}"

num_hist_in=`cat ${FILE_FREQ_IN} | wc -l`
num_hist_out=`cat ${FILE_FREQ_OUT} | wc -l`

cat "${FILE_FREQ_IN}" | cut -f 1 | sort > "${FILE_NAMES_IN}"
cat "${FILE_FREQ_OUT}" | cut -f 1 | sort > "${FILE_NAMES_OUT}"

echo "Number of unique syscalls (in/out): (${num_hist_in}/${num_hist_out}) - $(calc_percent ${num_hist_in} ${num_hist_out})% kept"

if [ ${num_hist_in} -gt ${num_hist_out} ]; then
  echo "Lost $((${num_hist_in}-${num_hist_out})) syscalls during translation"
  comm -23 "${FILE_NAMES_IN}" "${FILE_NAMES_OUT}" | sed 's/^/  /'
fi

# Total number of instances of syscalls
total_in=`cat ${FILE_FREQ_IN} | cut -f 2 | tr '\n' '+' | sed 's/+$/\n/'| bc`
total_out=`cat ${FILE_FREQ_OUT} | cut -f 2 | tr '\n' '+' | sed 's/+$/\n/'| bc`

echo "Total number of syscalls (in/out): (${total_in}/${total_out}) - $(calc_percent ${total_in} ${total_out})% kept"


# Compute Earth mover distance
EMD=0
if [ ${num_hist_in} -eq ${num_hist_out} ]; then
  i=0
  while [ $i -lt ${num_hist_in} ]; do
    cur_num_in=`head -n $(($i+1)) ${FILE_FREQ_IN} | tail -n 1 | cut -f 2`
    cur_num_out=`head -n $(($i+1)) ${FILE_FREQ_OUT} | tail -n 1 | cut -f 2`
    cur_diff=$((${cur_num_in}-${cur_num_out}))
    abs_diff=${cur_diff#-}
    EMD=$((${EMD} + ${abs_diff}))
    i=$(($i + 1))
  done
  echo "Earth movers distance: ${EMD}"
fi

# Info on visual meld diff
echo "Check Distribution differences"
echo "  meld ${FILE_FREQ_IN} ${FILE_FREQ_OUT}"
