# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

include(tmplr.cmake)
# TMPLR with default arguments
set(TMPLR_PROGRAM ${TMPLR_PROGRAM} -l 4096)
set(TMPLR_TARGET tmplr-build)
set(SINGLE_BM_TARGET csb-generate)
add_custom_target(${SINGLE_BM_TARGET})

# Since target SINGLE_BM_TARGET generates header files, we want to format these
# files right after the generation
add_custom_command(
    TARGET ${SINGLE_BM_TARGET}
    POST_BUILD
    COMMAND cmake --build "${CMAKE_BINARY_DIR}" --target clang-format-apply
            json-format-apply
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Find all single template files
file(GLOB TEMPLATES *single*.in)
# Collect all input headers
file(GLOB HEADERS CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/bench/targets/syz/*.h")
# Output dir for config files
set(CONFIG_DIR "${CMAKE_SOURCE_DIR}/config")
# Output dir for header files
set(HEADER_DIR "${CMAKE_SOURCE_DIR}/bench/targets")

# For each header input we want to generate a JSON config files and a matching
# header
foreach(HEADER ${HEADERS})
    # get header name without dir and extension
    get_filename_component(HEADER_NAME ${HEADER} NAME_WE)

    foreach(TEMPLATE ${TEMPLATES})
        # get template name without .in extension
        get_filename_component(TEMPLATE_NAME ${TEMPLATE} NAME_WLE)
        # find the real extension .h or .json
        get_filename_component(EXTENSION ${TEMPLATE_NAME} LAST_EXT)
        # based on the extension, decide target name, parameters to tmplr,
        # output file name, and path
        if(EXTENSION STREQUAL ".json")
            set(TARGET ${HEADER_NAME}_json)
            set(TMPLR_PARAMS -DPROBAVG="" -DPROBEND="1024"
                             -DBINNAME="${HEADER_NAME}")
            set(OUTPUT_FILE "${CONFIG_DIR}/${HEADER_NAME}.json")
        elseif(EXTENSION STREQUAL ".h")
            set(TARGET ${HEADER_NAME}_h)
            set(TMPLR_PARAMS -DNCALLS="1" -DNNOPS="1" -DNN="${HEADER_NAME}")
            set(OUTPUT_FILE "${HEADER_DIR}/${HEADER_NAME}.h")
        else()
            message(FATAL_ERROR "Unsupported extension ${EXTENSION}")
        endif()

        add_custom_target(${TARGET} COMMAND ${TMPLR_PROGRAM} ${TMPLR_PARAMS}
                                            ${TEMPLATE} > ${OUTPUT_FILE})
        # this target requires tmplr
        add_dependencies(${TARGET} ${TMPLR_TARGET})
        # the main target require this target
        add_dependencies(${SINGLE_BM_TARGET} ${TARGET})
    endforeach()
endforeach(HEADER)

# ##############################################################################
# Generate aggregated benchmark config: multi-app configuration file
# ##############################################################################
set(AGGREGATE_TARGET csb-gen-agg)
set(INPUT_TEMPLATE ${CMAKE_CURRENT_SOURCE_DIR}/syz_bm.json.in)
set(OUTPUT_FILE ${CONFIG_DIR}/aggregated.json)

# Find number of available files
list(LENGTH HEADERS FILES_NUM)

# Translate file names into application names
set(APPLICATIONS "")
foreach(HEADER ${HEADERS})
    get_filename_component(APP "${HEADER}" NAME_WE)
    list(APPEND APPLICATIONS "${APP}")
endforeach()
# Escape ; in order to be able to pass APPLICATIONS to tmplr
string(REPLACE ";" "\\;" APPLICATIONS "${APPLICATIONS}")
add_custom_target(
    ${AGGREGATE_TARGET}
    COMMAND ${TMPLR_PROGRAM} -DNN="${APPLICATIONS}" -DNPROCS="${FILES_NUM}"
            ${INPUT_TEMPLATE} > ${OUTPUT_FILE})
add_dependencies(${AGGREGATE_TARGET} ${TMPLR_TARGET})
add_custom_command(
    TARGET ${AGGREGATE_TARGET}
    POST_BUILD
    COMMAND cmake --build "${CMAKE_BINARY_DIR}" --target json-format-apply
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
