/*
 * Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
 * SPDX-License-Identifier: MIT
 */
#ifndef _HELPER_H_
#define _HELPER_H_

struct extracted_op {
    unsigned long n;
    unsigned long sz;
    bool is_write;
};

static inline long
parse_ops(const char *input, struct extracted_op *ops, size_t nops)
{
    const char *str = input;
    char *next      = NULL;
    size_t i        = 0;
    while (str[0] != 0 && i < nops) {
        unsigned long n = strtoul(str, &next, 10);
        bool is_write   = false;
        switch (next[0]) {
            default:
                return -1;
            case 'r':
                is_write = false;
                next++;
                break;
            case 'w':
                is_write = true;
                next++;
                break;
        }
        str              = next;
        unsigned long sz = strtoul(str, &next, 10);
        switch (next[0]) {
            default:
                return -2;
            case 0:
                break;
            case '-':
                next++;
                break;
        }
        str    = next;
        ops[i] = (struct extracted_op){
            .n        = n,
            .is_write = is_write,
            .sz       = sz,
        };
        i++;
    }
    return i;
}

static inline char *
load_prog_file(const char *path)
{
    int fd = open(path, O_RDONLY);
    if (fd == -1) {
        fprintf(stderr, "failed to open %s\n", path);
        return NULL;
    }
    struct stat st = {};
    int r          = fstat(fd, &st);
    if (r == -1) {
        fprintf(stderr, "failed to stat %s\n", path);
        return NULL;
    }
    void *data = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (data == MAP_FAILED) {
        fprintf(stderr, "failed to map %s\n", path);
        return NULL;
    }
    return data;
}

static inline size_t
get_max_buffer_size(struct extracted_op *ops, size_t nops)
{
    size_t max_sz = 0;
    for (size_t i = 0; i < nops; i++) {
        if (ops[i].sz > max_sz) {
            max_sz = ops[i].sz;
        }
    }
    return max_sz;
}

static inline void
setnonblocking(int sock)
{
    int opt = fcntl(sock, F_GETFL);
    if (opt < 0) {
        printf("fcntl(F_GETFL) fail.");
    }
    opt |= O_NONBLOCK;
    if (fcntl(sock, F_SETFL, opt) < 0) {
        printf("fcntl(F_SETFL) fail.");
    }
}

#endif /* _HELPER_H_ */
