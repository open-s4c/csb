#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT
 : ${FORCE:=0}
 : ${DIR_DESERIALIZED:="deserialized"}
 : ${DIR_EXTRACTED:="extracted"}
 : ${DIR_GENERATED_ROOT:="../bench/targets/gen-ws"}
 : ${DIR_CSB_BUILD:="../build"}

 : ${DIRS:="${DIR_DESERIALIZED} ${DIR_EXTRACTED} ${DIR_GENERATED_ROOT} ${DIR_CSB_BUILD}"}

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

if [ "$#" -eq 1 ]; then
    if [ "$1" == "-f" ]; then
        FORCE=1
    fi
fi

if [ ${FORCE} -eq 0 ]; then
    while true; do
        read -p "Do you wish to remove all generated files? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

for dir in ${DIRS}; do
    remove_dir "${dir}"
done

if [ ${FORCE} -eq 0 ]; then
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

echo "You probably want to run:"
echo "  (cd \"${DIR_BASE}\" && cmake -B \"$(basename ${DIR_CSB_BUILD})\" .);"
