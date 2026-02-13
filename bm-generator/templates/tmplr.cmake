# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

include(ExternalProject)
set(OPENS4C_URL "https://github.com/open-s4c")
set(TMPLR_VERSION "1.4.2")
set(TMPLR_URL "${OPENS4C_URL}/tmplr/archive/refs/tags/v${TMPLR_VERSION}.tar.gz")
set(TMPLR_SHA256
    "7f19dd58ccea737d9156f02167e2aa631218937195b3fbafe3475683bf9d888f")
set(TMPLR_PROGRAM "${CMAKE_BINARY_DIR}/tmplr/tmplr")

ExternalProject_Add(
    tmplr-build
    URL ${TMPLR_URL}
    URL_HASH SHA256=${TMPLR_SHA256}
    SOURCE_DIR "${CMAKE_BINARY_DIR}/tmplr"
    BINARY_DIR "${CMAKE_BINARY_DIR}/tmplr"
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${CMAKE_MAKE_COMMAND}
    INSTALL_COMMAND ""
    BUILD_BYPRODUCTS ${TMPLR_PROGRAM})

message(STATUS "TMPLR_PROGRAM will be at ${TMPLR_PROGRAM}")

add_custom_target(
    tmplr-check
    COMMAND ${TMPLR_PROGRAM} -V
    COMMENT "Running tmplr version check"
    DEPENDS tmplr-build)
