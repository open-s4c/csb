# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

include(FetchContent)

option(CSB_SYZKALLER_FETCH "Allows syzkaller fetching in cmake ON/OFF" OFF)

set(SYZKALLER syzkaller)
add_custom_target(${SYZKALLER})

if(CSB_SYZKALLER_FETCH)
    # An alternative to using syzkaller as a submodule
    FetchContent_Declare(
        ${SYZKALLER}
        GIT_REPOSITORY https://github.com/open-s4c/syzkaller.git
        GIT_TAG 7914e1189c073faed71ea695bac46dfb1111bd23
        GIT_PROGRESS TRUE
        EXCLUDE_FROM_ALL)

    FetchContent_MakeAvailable(${SYZKALLER})

    FetchContent_GetProperties(${SYZKALLER} SOURCE_DIR SYZKALLER_SOURCE_DIR)
else()
    set(SYZKALLER_SOURCE_DIR ${CMAKE_SOURCE_DIR}/deps/syzkaller)
endif()

find_program(GO_EXECUTABLE go)
if(NOT GO_EXECUTABLE)
    message(FATAL_ERROR "Go compiler not found. Please install Go.")
endif()
message(STATUS "Go found at: ${GO_EXECUTABLE}")

# Tools we want to build of syzkaller
set(TOOLS trace2syz prog2c extraction)
# Build each tool
foreach(TOOL ${TOOLS})
    add_custom_target(
        ${TOOL}
        COMMAND make ${TOOL}
        WORKING_DIRECTORY "${SYZKALLER_SOURCE_DIR}")
    add_dependencies(${SYZKALLER} ${TOOL})
endforeach(TOOL in ${TOOLS})

# Save syzkaller path to a file.
file(WRITE "${CMAKE_BINARY_DIR}/syzkaller-path.txt" "${SYZKALLER_SOURCE_DIR}")
add_subdirectory(templates)
