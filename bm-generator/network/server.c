#include <assert.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdbool.h>
#include <sys/epoll.h>
#include <getopt.h>
#include <errno.h>

#define MAX_EVS  16
#define MAX_SEND 1024
#define MAX_RECV 1024

static uint8_t sbuf[MAX_SEND];

struct serv_data {
    size_t step;
    int fd;
};

struct extracted_op {
    unsigned long n;
    unsigned long sz;
    bool is_write;
};

static void
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

static void
unregister(struct serv_data *d, int efd)
{
    epoll_ctl(efd, EPOLL_CTL_DEL, d->fd, NULL);
    close(d->fd);
    free(d);
}

static struct extracted_op eops[128];
static long eops_sz = 0;

static long
parse_ops(const char *input, struct extracted_op *ops, size_t nops)
{
    const char *str = input;
    char *next      = NULL;
    long i          = 0;
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

static void
config_wait(struct serv_data *d, int efd)
{
    size_t step = d->step;
    struct epoll_event ev_n;
    ev_n.events   = eops[step].is_write ? EPOLLIN : EPOLLOUT;
    ev_n.data.ptr = d;
    if (epoll_ctl(efd, EPOLL_CTL_MOD, d->fd, &ev_n) == -1) {
        perror("epoll_ctl_mod");
    }
}

static void
advance_step(struct serv_data *d)
{
    d->step = (d->step + 1) % eops_sz;
}

static void
readwrite(struct epoll_event *ev, int efd)
{
    struct serv_data *d = ev->data.ptr;
    int fd              = d->fd;
    int r;
    if (ev->events & (EPOLLHUP | EPOLLERR)) {
        unregister(d, efd);
        return;
    }
    if (ev->events & EPOLLOUT) {
        assert(!eops[d->step].is_write);
        assert(eops[d->step].n == 1);
        r = send(fd, &sbuf[0], eops[d->step].sz, 0);
    } else if (ev->events & EPOLLIN) {
        assert(eops[d->step].is_write);
        assert(eops[d->step].n == 1);
        r = recv(fd, &sbuf[0], eops[d->step].sz, 0);
    }
    if (r == -1) {
        unregister(d, efd);
        return;
    }

    advance_step(d);
    config_wait(d, efd);
}


int
main(int argc, char *argv[])
{
    size_t max_read  = 1024;
    size_t max_write = 1024;
    size_t port      = 10000;
    char *program    = NULL;
    char opt;
    while ((opt = getopt(argc, argv, "r:w:p:W:P:")) != -1) {
        switch (opt) {
            case 'w':
                max_write = strtoul(optarg, NULL, 0);
                if (errno == ERANGE || max_write > MAX_SEND) {
                    max_write = MAX_SEND;
                }
                break;
            case 'r':
                max_read = strtoul(optarg, NULL, 0);
                if (errno == ERANGE || max_read > MAX_RECV) {
                    max_read = MAX_RECV;
                }
                break;
            case 'p':
                port = strtoul(optarg, NULL, 0);
                if (errno == ERANGE) {
                    perror("strtoul");
                    return -1;
                }
                break;
            case 'P':
                program = optarg;
                break;
            default: /* '?' */
                fprintf(stderr,
                        "Usage: %s [-r max_read_bytes] [-w max_write_bytes] "
                        "[-W bytes_to_write_per_conn] "
                        "[-p port]\n",
                        argv[0]);
                return -1;
        }
    }

    if (!program) {
        return 'P';
    }
    eops_sz = parse_ops(program, &eops[0], sizeof(eops) / sizeof(eops[0]));
    if (eops_sz < 0) {
        return 'P';
    }

    struct epoll_event ev;
    int efd = epoll_create1(0);
    if (efd == -1) {
        return 1;
    }
    int lsock = socket(AF_INET, SOCK_STREAM, 0);
    if (lsock == -1) {
        return 1;
    }

    struct sockaddr_in loopback = {
        .sin_family      = AF_INET,
        .sin_addr.s_addr = htonl(INADDR_ANY),
        .sin_port        = htons(port),
    };

    if (bind(lsock, (struct sockaddr *)&loopback, sizeof(loopback)) == -1) {
        return 2;
    }
    if (listen(lsock, 50) == -1) {
        return 2;
    }
    ev.events   = EPOLLIN;
    ev.data.ptr = NULL;
    if (epoll_ctl(efd, EPOLL_CTL_ADD, lsock, &ev) == -1) {
        return -1;
    }
    while (true) {
        struct epoll_event evs[MAX_EVS];
        int nfds = epoll_wait(efd, &evs[0], MAX_EVS, -1);
        if (nfds == -1) {
            perror("epoll_wait");
            continue;
        }
        for (int i = 0; i < nfds; i++) {
            if (evs[i].data.ptr == NULL) {
                int cfd = accept(lsock, NULL, 0);
                if (cfd == -1) {
                    perror("accept");
                    continue;
                }
                setnonblocking(cfd);
                struct serv_data *d = malloc(sizeof(struct serv_data));
                if (!d) {
                    perror("malloc");
                    close(cfd);
                    continue;
                }
                d->fd       = cfd;
                d->step     = 0;
                ev.events   = eops[0].is_write ? EPOLLIN : EPOLLOUT;
                ev.data.ptr = d;
                if (epoll_ctl(efd, EPOLL_CTL_ADD, cfd, &ev) == -1) {
                    perror("epoll_ctl");
                    close(cfd);
                    free(d);
                    continue;
                }
            } else {
                readwrite(&evs[i], efd);
            }
        }
    }
    return 0;
}
