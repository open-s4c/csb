# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

file(GLOB AGENTS CONFIGURE_DEPENDS *.c)

foreach(AGENT ${AGENTS})
    message(STATUS "Adding agent ${AGENT}")
    get_filename_component(AGENT_NAME ${AGENT} NAME_WLE)
    add_executable(${AGENT_NAME} ${AGENT})
    target_compile_options(${AGENT_NAME} PRIVATE "-g")
    if(${AGENT_NAME} STREQUAL "redis-client")
        target_link_libraries(${AGENT_NAME} hiredis)
    endif()
endforeach(AGENT)

add_test(NAME client-server-comm
         COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/test-comm.sh)
