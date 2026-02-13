# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

include(FetchContent)

message(STATUS "Fetching syzkaller ...")

set(TARGET_NAME syz)
set(SYZKALLER syzkaller)

FetchContent_Declare(
    ${SYZKALLER}
    GIT_REPOSITORY https://github.com/open-s4c/syzkaller.git
    GIT_TAG bf8bf3b26909a630a4a582ddaabaccdc6756bbb6
    GIT_PROGRESS TRUE
    EXCLUDE_FROM_ALL)

FetchContent_MakeAvailable(${SYZKALLER})

FetchContent_GetProperties(${SYZKALLER} SOURCE_DIR SYZKALLER_SOURCE_DIR)
message("${SYZKALLER_SOURCE_DIR}")
find_program(GO_EXECUTABLE go)
if(NOT GO_EXECUTABLE)
    message(FATAL_ERROR "Go compiler not found. Please install Go.")
endif()
message(STATUS "Go found at: ${GO_EXECUTABLE}")

# build syzkaller
add_custom_target(
    ${TARGET_NAME}
    COMMAND make
    WORKING_DIRECTORY ${SYZKALLER_SOURCE_DIR})

set(TOOLS_DIR "${SYZKALLER_SOURCE_DIR}/tools")
# Tools we want to build of syzkaller
set(TOOLS trace2syz prog2c extraction)
# Build each tool
foreach(TOOL IN ITEMS ${TOOLS})
    set(TOOL_NAME syz-${TOOL})
    add_custom_target(
        ${TOOL}
        COMMAND go build
        WORKING_DIRECTORY "${TOOLS_DIR}/${TOOL_NAME}")
endforeach(TOOL in ${TOOLS})

# Save syzkaller path to a file.
file(WRITE "${CMAKE_BINARY_DIR}/syzkaller-path.txt" "${SYZKALLER_SOURCE_DIR}")

add_subdirectory(templates)
