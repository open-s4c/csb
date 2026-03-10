#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
 : ${ALL:=0}
 : ${FORCE:=0}

 : ${DIR_DESERIALIZED:="deserialized"}
 : ${DIR_EXTRACTED:="extracted"}
 : ${DIR_GENERATED_ROOT:="../bench/targets/gen-ws"}
 : ${DIR_CONFIG:="../config/gen-ws"}
 : ${DIR_CSB_BUILD:="../build"}

 : ${DIRS_ALL:="${DIR_DESERIALIZED} ${DIR_EXTRACTED} ${DIR_GENERATED_ROOT} ${DIR_CSB_BUILD} ${DIR_CONFIG}"}
 : ${DIRS_DEFAULT:="${DIR_GENERATED_ROOT} ${DIR_CONFIG}"}
 : ${DIRS:=${DIRS_DEFAULT}}

dry_run=1

remove_dir() {
    if [ "$#" -ne 1 ]; then
        return
    fi
    DIR="$1"
    DIR_ABS="$(readlink -e ${DIR})"

    if [ ! -d "${DIR_ABS}" ]; then
        echo "  $DIR is not a directory"
        return
    fi

    if [ "${dry_run}" -eq 1 ]; then
        echo "[dry_run] rm -rf ${DIR_ABS}"
    else
        rm -rf ${DIR_ABS}
    fi
}

while [ "$#" -gt 0 ]; do
    if [ "$1" == "-f" ]; then
        FORCE=1
    fi
    if [ "$1" == "-a" ]; then
        ALL=1
    fi
    shift
done

if [ ${ALL} -eq 0 ]; then
    DIRS="${DIRS_DEFAULT}"
else
    DIRS="${DIRS_ALL}"
fi

if [ ${FORCE} -eq 0 ]; then
    for dir in ${DIRS}; do
        remove_dir "${dir}"
    done
    while true; do
        read -p "Do you wish to remove all shown paths? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

dry_run=0
for dir in ${DIRS}; do
    remove_dir "${dir}"
done

DIR_BASE="$(readlink -e ${DIR_CSB_BUILD}/..)"

if [ "x${DIR_BASE}" == "x" ]; then
    DIR_BASE="$(dirname ${DIR_CSB_BUILD})"
fi

if [ ${ALL} -eq 1 ]; then
    echo "You probably want to run:"
    echo "  (cd \"${DIR_BASE}\" && cmake -B \"$(basename ${DIR_CSB_BUILD})\" .);"
fi