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


#
# Needed due to pandas issues with timestamps
#
RUN dnf install -y glibc-all-langpacks cmake perf sysstat sudo gcc \
                   moby-engine moby-client hiredis-devel jq \
                   hostname python3 python3-pip iproute lshw ethtool \
                   nvme-cli hdparm libcgroup-tools sudo git

#
# Reduce container disk space by dropping dnf data
#
RUN dnf clean all

#
# Docker-specific setup: install sudo disabling PAM authentication
#
RUN set -eux; \
    echo 'auth sufficient pam_permit.so' > /etc/pam.d/sudo && \
    echo 'account sufficient pam_permit.so' >> /etc/pam.d/sudo && \
    echo 'session sufficient pam_permit.so' >> /etc/pam.d/sudo && \
    echo 'Double check if sudo works' | sudo tee /tmp/sudo_test.txt

#
# Directory used when running containers inside CSB.
# This needs to be mapped by the host as otherwise container tests won't run.
#
RUN mkdir -p /venv

#
# Prepare the environment: initialize git submodules and venv
#
#COPY . .
RUN ./scripts/prepare.sh

#
# Copy virtualenv to the container
#
RUN mv ./venv /venv

CMD ["bash"]
