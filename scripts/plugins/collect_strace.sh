#!/bin/bash
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT


FILE_LOG=$1
shift

 : ${GDB_SCRIPT:="syscall_addresses.gdb"}
 : ${GDB_LOG:="syscall_addresses.log"}

LOG_SYSCALL_x86_64='
define log_syscall
    printf "Syscall at %p\n", $rip
    printf "arg1 (rdi): %p\n", $rdi
    printf "arg2 (rsi): %p\n", $rsi
    printf "arg3 (rdx): %p\n", $rdx
    printf "arg4 (r10): %p\n", $r10
    printf "arg5 (r8): %lx\n", $r8
    printf "arg6 (r9): %lx\n", $r9
end
'

LOG_SYSCALL_ARM64='
define log_syscall
    printf "Syscall at %p\n", $pc
    printf "arg1 (x0): %p\n", $x0
    printf "arg2 (x1): %p\n", $x1
    printf "arg3 (x2): %p\n", $x2
    printf "arg4 (x3): %p\n", $x3
    printf "arg5 (x4): %p\n", $x4
    printf "arg6 (x5): %p\n", $x5
    printf "arg7 (x6): %p\n", $x6
    printf "arg8 (x7): %p\n", $x7
end
'
LOG_SYSCALL_AARCH64=${LOG_SYSCALL_ARM64}

ARCH=$(uname -m)
LOG_SYSCALL=${LOG_SYSCALL_x86_64}

write_gdb_script() {
/bin/cat <<EOM >${GDB_SCRIPT}
set follow-fork-mode child
set logging file ${GDB_LOG}
set logging overwrite on
set logging redirect on
set logging enabled on

${LOG_SYSCALL}

set \$in_syscall = 0

define set_breakpoints
    catch syscall
    commands
        if \$in_syscall == 0
          set \$in_syscall = 1
          log_syscall
        else
          set \$in_syscall = 0
        end
        continue
    end
end

catch fork
commands
    set_breakpoints
    continue
end

set_breakpoints

run

exit

EOM
}

if [ -z "`command -v strace`" ]; then
  echo "\"strace\" command not found in \$PATH. Either install strace or add it to PATH"
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage:"
  echo "  $0 <output_fname> <command> [<arg1>] [<arg2>] ..."
  exit 1
fi

if [ -f "${FILE_LOG}" ]; then
  echo "Output file \"${FILE_LOG}\" already exists. (re)move it, or use a different output file name. Example:"
  echo "  FILE_LOG=strace_output.log $0 $@"
  exit 1
fi

write_gdb_script
gdb -x "${GDB_SCRIPT}" --args \
strace -o "${FILE_LOG}" -a 1 -s 65500 -v -xx -f -Xraw --raw=wait4 $@
