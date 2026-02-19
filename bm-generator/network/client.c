#include <arpa/inet.h>
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

struct extracted_op {
    unsigned long n;
    unsigned long sz;
    bool is_write;
};

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

#define MAX_EVS  16
#define MAX_SEND 1024
#define MAX_RECV 1024

static uint8_t sbuf[MAX_SEND];

struct serv_data {
    size_t step;
    int last_epoll;
    int fd;
};

struct epoll_st {
    int fd;
    size_t nconn;
};

static void
config_wait(struct serv_data *d, struct epoll_st *est)
{
    size_t step = d->step;
    int next_epoll = eops[step].is_write ? EPOLLOUT : EPOLLIN;
    if (d->last_epoll == next_epoll) {
        return;
    }
    struct epoll_event ev_n;
    ev_n.events   = next_epoll;
    ev_n.data.ptr = d;
    d->last_epoll = next_epoll;
    if (epoll_ctl(est->fd, EPOLL_CTL_MOD, d->fd, &ev_n) == -1) {
        perror("epoll_ctl_mod");
    }
}

static void
advance_step(struct serv_data *d)
{
    d->step = (d->step + 1) % eops_sz;
}

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
unregister(struct serv_data *d, struct epoll_st *est)
{
    epoll_ctl(est->fd, EPOLL_CTL_DEL, d->fd, NULL);
    close(d->fd);
    free(d);
    est->nconn--;
}

static void
readwrite(struct epoll_event *ev, struct epoll_st *est)
{
    struct serv_data *d = ev->data.ptr;
    int fd              = d->fd;
    int r;
    if (ev->events & (EPOLLHUP | EPOLLERR)) {
        unregister(d, est);
        return;
    }

    if (ev->events & EPOLLOUT) {
        assert(eops[d->step].is_write);
        assert(eops[d->step].n == 1);
        r = send(fd, &sbuf[0], eops[d->step].sz, 0);
    } else if (ev->events & EPOLLIN) {
        assert(!eops[d->step].is_write);
        assert(eops[d->step].n == 1);
        r = recv(fd, &sbuf[0], eops[d->step].sz, 0);
    }
    if (r == -1) {
        unregister(d, est);
        return;
    }
    advance_step(d);
    if (0 && d->step == 0) {
        unregister(d, est);
        return;
    } else {
        config_wait(d, est);
    }
}


int
main(int argc, char *argv[])
{
    size_t num_conn  = 1;
    size_t max_read  = 1024;
    size_t max_write = 1024;
    size_t port      = 10000;
    char *host       = NULL;
    char *program    = NULL;
    char opt;
    while ((opt = getopt(argc, argv, "h:r:w:p:W:P:")) != -1) {
        switch (opt) {
            case 'h':
                host = optarg;
                break;
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

    if (!host) {
        fprintf(stderr, "No host specified\n");
        return 1;
    }

    struct addrinfo *result = NULL;
    struct addrinfo hints   = {
          .ai_family   = PF_UNSPEC,
          .ai_socktype = SOCK_STREAM,
          .ai_flags    = AI_CANONNAME,
    };
    int r = getaddrinfo(host, NULL, &hints, &result);
    if (r == -1) {
        fprintf(stderr, "getaddrinfo: %s", gai_strerror(r));
        return 1;
    }

    struct sockaddr *serv_addr = NULL;
    for (struct addrinfo *res = result; res != NULL; res = res->ai_next) {
        char addrstr[100];
        switch (res->ai_family) {
            case AF_INET:
                serv_addr                                   = res->ai_addr;
                ((struct sockaddr_in *)serv_addr)->sin_port = htons(port);
                break;
            default:
                continue;
        }
        inet_ntop(res->ai_family,
                  &((struct sockaddr_in *)res->ai_addr)->sin_addr, addrstr,
                  100);
        printf("IPv4 address: %s (%s)\n", addrstr, res->ai_canonname);
        break;
    }

    struct epoll_event ev;
    struct epoll_st est = {};
    est.fd              = epoll_create1(0);
    if (est.fd == -1) {
        return 1;
    }

    for (size_t i = 0; i < num_conn; i++) {
        struct serv_data *d = malloc(sizeof(struct serv_data));
        if (!d) {
            return 13;
        }
        d->step       = 0;
        d->last_epoll = eops[0].is_write ? EPOLLOUT : EPOLLIN;

        int csock = socket(AF_INET, SOCK_STREAM, 0);
        if (csock == -1) {
            return 1;
        }
        d->fd = csock;

        if (connect(csock, serv_addr, sizeof(struct sockaddr_in)) == -1) {
            return 2;
        }

        setnonblocking(csock);

        ev.events   = d->last_epoll;
        ev.data.ptr = d;
        if (epoll_ctl(est.fd, EPOLL_CTL_ADD, csock, &ev) == -1) {
            return -1;
        }
        est.nconn++;
    }

    while (est.nconn) {
        struct epoll_event evs[MAX_EVS];
        int nfds = epoll_wait(est.fd, &evs[0], MAX_EVS, -1);
        if (nfds == -1) {
            perror("epoll_wait");
            continue;
        }
        for (int i = 0; i < nfds; i++) {
            readwrite(&evs[i], &est);
        }
    }
    return 0;
}
