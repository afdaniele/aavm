# parameters
ARG ARCH
ARG NAME
ARG ORGANIZATION
ARG DESCRIPTION
ARG MAINTAINER

# ==================================================>
# ==> Do not change the code below this line
ARG BASE_REGISTRY=docker.io
ARG BASE_ORGANIZATION=afdaniele
ARG BASE_REPOSITORY=aavm
ARG BASE_TAG=ubuntu-20.04

# define base image
FROM ${BASE_REGISTRY}/${BASE_ORGANIZATION}/${BASE_REPOSITORY}:${BASE_TAG}-${ARCH} as BASE

# recall all arguments
# - current project
ARG ARCH
ARG NAME
ARG ORGANIZATION
ARG DESCRIPTION
ARG MAINTAINER
# - base project
ARG BASE_REGISTRY
ARG BASE_ORGANIZATION
ARG BASE_REPOSITORY
ARG BASE_TAG

# define/create project paths
ARG PROJECT_PATH="${CPK_SOURCE_DIR}/${NAME}"
RUN mkdir -p "${PROJECT_PATH}"
WORKDIR "${PROJECT_PATH}"

# install apt dependencies
COPY ./dependencies-apt.txt "${PROJECT_PATH}/"
RUN cpk-apt-install ${PROJECT_PATH}/dependencies-apt.txt

# install python3 dependencies
COPY ./dependencies-py3.txt "${PROJECT_PATH}/"
RUN cpk-pip3-install ${PROJECT_PATH}/dependencies-py3.txt

# copy project root
COPY ./*.cpk ./*.sh ${PROJECT_PATH}/
# <== Do not change the code above this line
# <==================================================

# copy components
COPY assets/components "${AAVM_DIR}/components/available"

# install components
# - Docker
RUN aavm-component-install docker
LABEL aavm.environment.components.docker="1"

# - Docker Compose
RUN aavm-component-install docker-compose
LABEL aavm.environment.components.docker-compose="1"

# - Docker Buildx
RUN aavm-component-install docker-buildx
LABEL aavm.environment.components.docker-buildx="1"

# store aavm metadata
LABEL \
    aavm.runtime="1" \
    aavm.environment.os_family="linux" \
    aavm.environment.arch="${ARCH}" \
    aavm.environment.description="${DESCRIPTION}" \
    aavm.environment.maintainer="${MAINTAINER}"
