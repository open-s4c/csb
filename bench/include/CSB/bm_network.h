/*
 * Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
 * SPDX-License-Identifier: MIT
 */
#ifndef BM_NETWORK_H
#define BM_NETWORK_H

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <stdbool.h>

static struct sockaddr_in bm_connect_addr;
static bool bm_connect_addr_inited;

static struct sockaddr_in bm_bind_addr;
static bool bm_bind_addr_inited = false;

static inline void
parse_net_addr(const char *addr_env, const char *port_env,
               struct sockaddr_in *dst, bool *inited)
{
    const char *conn_addr_str = getenv(addr_env);
    const char *conn_port_str = getenv(port_env);
    if (conn_addr_str) {
        dst->sin_family = AF_INET;
        dst->sin_port   = htons(31334);
        int r =
            inet_pton(dst->sin_family, conn_addr_str, &dst->sin_addr.s_addr);
        if (r == 1) {
            *inited = true;
        } else if (r == -1) {
            perror("inet_pton(connect addr)");
            exit(-1);
        } else {
            fprintf(stderr,
                    "inet_pton(connect addr): Not in presentation format.");
            exit(-1);
        }
    }
    if (*inited && conn_port_str) {
        unsigned long port = strtoul(conn_port_str, NULL, 0);
        if (errno == ERANGE) {
            perror("strtoul(conn_port_str)");
            exit(-1);
        }
        dst->sin_port = htons(port);
    }
}


#endif
