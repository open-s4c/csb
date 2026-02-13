cmake_minimum_required(VERSION 3.22)

project(
    CSB
    LANGUAGES C
    DESCRIPTION "Builtin Benchmarks of CSB")

add_subdirectory(bench)

# TODO: add based on a cmake option! or fetch syzkaller on demand
add_subdirectory(bm-generator)

set(HELPERS ${CMAKE_SOURCE_DIR}/helpers)

# Add clang-format target
set(CLANG_STYLE_FILE ${HELPERS}/.clang-format)

set(CLANG_FMT_CMD ${HELPERS}/clang-format.sh ${CMAKE_SOURCE_DIR})

add_custom_target(clang-format-apply COMMAND env STYLE=${CLANG_STYLE_FILE}
                                             SILENT=true ${CLANG_FMT_CMD}
                                    WORKING_DIRECTORY  ${CMAKE_SOURCE_DIR}
                                             )

set(CMAKE_FMT_CMD ${HELPERS}/cmake-format.sh ${CMAKE_SOURCE_DIR})

set(CMAKE_STYLE_FILE ${HELPERS}/.cmake-format)

add_custom_target(cmake-format-apply COMMAND env STYLE=${CMAKE_STYLE_FILE}
                                             SILENT=true ${CMAKE_FMT_CMD})

add_custom_target(git-diff-check COMMAND git --no-pager diff --exit-code)
