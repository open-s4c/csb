#!/bin/bash -e
# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

LOCAL_BUILD=
NAME="openeuler-csb-test"
DOCKER_IMAGE="openeuler_for_csb:latest"
REPOSITORY="ghcr.io/open-s4c/csb"
DOCKERFILE=".github/workflows/docker/openeuler-for-csb.Dockerfile"
SHELL=
TEST=bm_empty

usage() {
  cat <<'EOF'
Usage: $(basename "$0") [options]

Options:
  --local-build,-l          Build the Docker image locally (default: pull)
  --docker-image,-I IMAGE   Use the given Docker image instead of the default
  --shell,-s                Start an interactive bash shell in the container
  --test, -t                Test name
  --help,-h                 Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-build|-l)
      LOCAL_BUILD=1
      ;;
    --docker-image|-I)
      shift
      DOCKER_IMAGE="$1"
      ;;
    --test|-t)
      shift
      TEST="$1"
      ;;
    --shell|-s)
      SHELL=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if [ ! -z "${LOCAL_BUILD}" ]; then
  echo "Building ${DOCKER_IMAGE}"
  docker buildx build --tag "${DOCKER_IMAGE}" --file ${DOCKERFILE} .
else
  echo "Pulling container from ${REPOSITORY}/${DOCKER_IMAGE}"
  docker pull "${REPOSITORY}/${DOCKER_IMAGE}"
  docker tag "${REPOSITORY}/${DOCKER_IMAGE}" "${DOCKER_IMAGE}"
fi

if [ ! -z "${SHELL}" ]; then
  echo "Opening a shell"
  docker run --rm --name ${NAME} \
    -v /boot:/boot -v /lib/modules:/lib/modules \
    -v /tmp/csb:/home/csb \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -it "${DOCKER_IMAGE}" bash
else
  echo "Running test config/${TEST}.json"
  docker run --rm --name ${NAME} \
    -v /boot:/boot -v /lib/modules:/lib/modules \
    -v /tmp/csb:/home/csb \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -it "${DOCKER_IMAGE}" \
    bash -c "cd /home/csb && git config --global --add safe.directory /home/csb && scripts/fg-diff/run-single.sh config/${TEST}.json"
fi
