# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

add_library(CSB INTERFACE)

target_include_directories(
    CSB INTERFACE "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
                  "$<INSTALL_INTERFACE:include>")

option(CSB_ADDRESS_SANITIZER "Compile with -fsanitize=address" "off")
option(CSB_THREAD_SANITIZER "Compile with -fsanitize=thread" "off")

if(CSB_ADDRESS_SANITIZER)
    target_compile_options(CSB INTERFACE -fsanitize=address,undefined)
    target_link_options(CSB INTERFACE -fsanitize=address,undefined)
elseif(CSB_THREAD_SANITIZER)
    target_compile_options(CSB INTERFACE -fsanitize=thread)
    target_link_options(CSB INTERFACE -fsanitize=thread)
endif()

enable_testing()
file(GLOB TARGETS targets/*.h)

set(BM_DEFS _GNU_SOURCE)

set(BM_PARAM
    "-t=1"
    "-n=0" # noise
    "-d=2" # duration
    "-s=100" # initial size
    "-op0=1024" # op0 freq in /1024
)

set(BM_PARAM_bm_server_redis
    "-t=1"
    "-n=0" # noise
    "-d=1" # duration
    "-s=5000" # used as port
    "-op0=500" # op0 freq in /1024
    "-op1=524" # op1 freq in /1024
)

set(BM_PARAM_bm_empty
    "-t=12"
    "-n=0" # noise
    "-d=1" # duration
    "-s=0" # initial size
    "-op0=1024" # op0 freq in /1024
)

set(BM_FILE benchmark.c)

foreach(target IN ITEMS ${TARGETS})
    get_filename_component(bm_target_prefix ${target} NAME_WLE)
    set(bm_target_name "\"${target}\"")
    set(TEST_CASE ${bm_target_prefix})

    string(TOLOWER ${TEST_CASE} TEST_CASE)

    add_executable(${TEST_CASE} ${BM_FILE})

    target_link_libraries(${TEST_CASE} pthread CSB)

    target_compile_definitions(${TEST_CASE} PUBLIC ${BM_DEFS}
                                                   BM_TARGET=${bm_target_name})

    target_compile_options(${TEST_CASE} PUBLIC -g -O2 -Wall -Werror
                                               -Wno-unused-function)

    if(DEFINED BM_PARAM_${bm_target_prefix})
        set(PARAMS ${BM_PARAM_${bm_target_prefix}})
    else()
        set(PARAMS ${BM_PARAM})
    endif()
    # add the bm as a test
    add_test(NAME ${TEST_CASE} COMMAND ${TEST_CASE} ${PARAMS})
endforeach()

# Compile client
set(CLIENT_NAME "client")
add_executable(${CLIENT_NAME} client.c)
target_link_libraries(${CLIENT_NAME} hiredis)
