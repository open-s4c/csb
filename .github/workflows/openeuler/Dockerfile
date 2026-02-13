# syntax=docker/dockerfile:1
#
# Base image
#
ARG BASE_IMAGE=openeuler/openeuler:24.03-lts-sp3
ARG TARGET=amd64

FROM ${BASE_IMAGE}

#
# To create and run it direcly, use:
#    docker build -t openeuler-csb:latest -f .github/workflows/openeuler/Dockerfile .
#    docker run -v /var/run/docker.sock:/var/run/docker.sock -it openeuler-csb:latest bash
#
# Note, however, that csb is currently not ready to run like that
#


# Needed volumes. The first two are used by get info scripts
VOLUME [ "/boot", "/lib/modules", "/var/run/docker.sock" ]

#
# Needed due to pandas issues with timestamps
#
RUN dnf install -y glibc-all-langpacks

#
# Dependencies from doc/bm-runner.md
#
RUN dnf install -y cmake perf sysstat sudo gcc moby-engine moby-client hiredis-devel jq

#
# Currently undocumented dependencies
#
RUN dnf install -y hostname python3 python3-pip iproute lshw ethtool nvme-cli hdparm libcgroup-tools stress-ng fio

#
# Docker-specific setup: install sudo disabling PAM authentication
#
RUN set -eux; \
    dnf install -y sudo; \
    echo 'auth sufficient pam_permit.so' > /etc/pam.d/sudo && \
    echo 'account sufficient pam_permit.so' >> /etc/pam.d/sudo && \
    echo 'session sufficient pam_permit.so' >> /etc/pam.d/sudo && \
    echo 'Double check if sudo works' | sudo tee /tmp/sudo_test.txt

#
# Git is needed to clone the repository inside the container
#
RUN dnf install -y git

#
# Reduce container disk space by dropping dnf data
#
RUN dnf clean all

# Create a working directory and update submodules
WORKDIR /root/csb
COPY . .

#
# Prepare the environment: initialize git submodules and venv
#
RUN ./scripts/prepare.sh

CMD ["/root/csb/run.sh"]
