include(tmplr.cmake)
set(TMPLR_PROGRAM ${TMPLR_PROGRAM} -l 4096)
set(CONFIG_ARGS )

add_custom_target(csb-generate)

# find all template inputs
file(GLOB TEMPLATES *single*.in)
file(GLOB HEADERS "${CMAKE_SOURCE_DIR}/../bench/targets/syz/*.h")

set(CONFIG_DIR "${CMAKE_SOURCE_DIR}/../config")
set(HEADER_DIR "${CMAKE_SOURCE_DIR}/../bench/targets")

foreach(HEADER ${HEADERS})
    get_filename_component(HEADER_NAME ${HEADER} NAME_WE)
    foreach(TEMPLATE ${TEMPLATES})
        get_filename_component(TEMPLATE_NAME ${TEMPLATE} NAME_WLE)
        get_filename_component(EXTENSION ${TEMPLATE_NAME} LAST_EXT)

        if(EXTENSION STREQUAL ".json")
            set(TARGET ${HEADER_NAME}_json)
            set(CMD -DPROBAVG="" -DPROBEND="1024" -DBINNAME="${HEADER_NAME}")
            set(OUTPUT_FILE "${CONFIG_DIR}/${HEADER_NAME}.json")
        elseif(EXTENSION STREQUAL ".h")
            set(TARGET ${HEADER_NAME})
            set(CMD -DNCALLS="1" -DNNOPS="1" -DNN="${HEADER_NAME}")
            set(OUTPUT_FILE "${HEADER_DIR}/${HEADER_NAME}.h")
        else()
            message(FATAL_ERROR "Unsupported extension ${EXTENSION}")
        endif()

        add_custom_target(
            ${TARGET} COMMAND ${TMPLR_PROGRAM} ${CMD} ${TEMPLATE} > ${OUTPUT_FILE})

        add_dependencies(${TARGET} tmplr-build)
        add_dependencies(csb-generate ${TARGET})
    endforeach()
endforeach(HEADER)

# Find out how many files are there
list(LENGTH HEADERS FILES_NUM)

# string(JOIN ";" APPLICATIONS ${HEADERS})
# string(REPLACE ";" "\\;" APPLICATIONS "${APPLICATIONS}")
# message("${APPLICATIONS}")

set(APPLICATIONS "")
foreach(HEADER IN LISTS HEADERS)
    get_filename_component(APP "${HEADER}" NAME_WE)
    list(APPEND APPLICATIONS "${APP}")
endforeach()

string(REPLACE ";" "\\;" APPLICATIONS "${APPLICATIONS}")

message("${APPLICATIONS}")

add_custom_target(
    csb-generate-agg COMMAND ${TMPLR_PROGRAM} -DNN="${APPLICATIONS}" -DNPROCS="${FILES_NUM}" ${CMAKE_CURRENT_SOURCE_DIR}/syz_bm.json.in > ${CONFIG_DIR}/aggregated.json
)
