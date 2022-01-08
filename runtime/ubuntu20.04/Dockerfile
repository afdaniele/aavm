# parameters
ARG ARCH
ARG NAME
ARG ORGANIZATION
ARG DESCRIPTION
ARG MAINTAINER

# ==================================================>
# ==> Do not change the code below this line
ARG BASE_REGISTRY=docker.io
ARG BASE_ORGANIZATION=cpkbase
ARG BASE_REPOSITORY=ubuntu
ARG BASE_TAG=focal

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
# - defaults
ARG LAUNCHER=default

# define/create project paths
ARG PROJECT_PATH="${CPK_SOURCE_DIR}/${NAME}"
ARG PROJECT_LAUNCHERS_PATH="${CPK_LAUNCHERS_DIR}/${NAME}"
RUN mkdir -p "${PROJECT_PATH}"
RUN mkdir -p "${PROJECT_LAUNCHERS_PATH}"
WORKDIR "${PROJECT_PATH}"

# keep some arguments as environment variables
ENV \
    CPK_PROJECT_NAME="${NAME}" \
    CPK_PROJECT_DESCRIPTION="${DESCRIPTION}" \
    CPK_PROJECT_MAINTAINER="${MAINTAINER}" \
    CPK_PROJECT_PATH="${PROJECT_PATH}" \
    CPK_PROJECT_LAUNCHERS_PATH="${PROJECT_LAUNCHERS_PATH}" \
    CPK_LAUNCHER="${LAUNCHER}"

# install apt dependencies
COPY ./dependencies-apt.txt "${PROJECT_PATH}/"
RUN cpk-apt-install ${PROJECT_PATH}/dependencies-apt.txt

# install python3 dependencies
COPY ./dependencies-py3.txt "${PROJECT_PATH}/"
RUN cpk-pip3-install ${PROJECT_PATH}/dependencies-py3.txt

# install launcher scripts
COPY ./launchers/. "${PROJECT_LAUNCHERS_PATH}/"
COPY ./launchers/default.sh "${PROJECT_LAUNCHERS_PATH}/"
RUN cpk-install-launchers "${PROJECT_LAUNCHERS_PATH}"

# copy project root
COPY ./*.cpk ./*.sh ${PROJECT_PATH}/

# copy the source code
COPY ./packages "${CPK_PROJECT_PATH}/packages"

# define default command
CMD ["bash", "-c", "launcher-${CPK_LAUNCHER}"]

# store module metadata
LABEL \
    cpk.label.current="${ORGANIZATION}.${NAME}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.description="${DESCRIPTION}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.code.location="${PROJECT_PATH}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.base.registry="${BASE_REGISTRY}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.base.organization="${BASE_ORGANIZATION}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.base.project="${BASE_REPOSITORY}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.base.tag="${BASE_TAG}" \
    cpk.label.project.${ORGANIZATION}.${NAME}.maintainer="${MAINTAINER}"
# <== Do not change the code above this line
# <==================================================

# install QEMU (amd only)
RUN set -eu; \
	case "$ARCH" in \
        # amd64
		amd64) apt-get update; \
               apt-get install -y --no-install-recommends qemu binfmt-support qemu-user-static; \
               rm -rf /var/lib/apt/lists/* ;; \
        # any other
		*) echo >&2 "QEMU not supported on architecture ($ARCH)" ;;\
	esac;

# make aavm service directory
ENV AAVM_DIR "/aavm"
RUN mkdir \
    "${AAVM_DIR}" \
    "${AAVM_DIR}/components" \
    "${AAVM_DIR}/components/available" \
    "${AAVM_DIR}/components/installed"

# make aavm user
ENV AAVM_USER="user" \
    AAVM_USER_UID=1000 \
    AAVM_USER_GID=1000 \
    AAVM_USER_SHELL="/bin/bash" \
    AAVM_USER_PASSWORD="password"
ENV AAVM_USER_HOME="/home/${AAVM_USER}"
RUN addgroup --system privileged && \
    addgroup --gid ${AAVM_USER_GID} "${AAVM_USER}" && \
    useradd \
        --create-home \
        --home-dir "${AAVM_USER_HOME}" \
        --comment "AAVM User" \
        --shell "${AAVM_USER_SHELL}" \
        --password "papAq5PwY/QQM" \
        --uid ${AAVM_USER_UID} \
        --gid ${AAVM_USER_GID} \
        --groups privileged \
        "${AAVM_USER}"

# give the user access to the cpk environment
# - for interactive bash sessions
RUN echo "source ${CPK_INSTALL_DIR}/environment.sh" >> "${AAVM_USER_HOME}/.bashrc"
# - for non-interactive bash sessions
ENV BASH_ENV "${CPK_INSTALL_DIR}/environment.sh"

# constants
RUN echo "\
export AAVM_DIR=\"${AAVM_DIR}\" \n\
export AAVM_USER=\"${AAVM_USER}\" \n\
export AAVM_USER_UID=\"${AAVM_USER_UID}\" \n\
export AAVM_USER_GID=\"${AAVM_USER_GID}\" \n\
export AAVM_USER_SHELL=\"${AAVM_USER_SHELL}\" \n\
export AAVM_USER_HOME=\"${AAVM_USER_HOME}\" \
" > "${AAVM_DIR}/constants.sh"

# remove all unused systemd units
RUN cd /lib/systemd/system/sysinit.target.wants/; \
    ls | grep -v systemd-tmpfiles-setup | xargs rm -f $1 \
    rm -f /lib/systemd/system/multi-user.target.wants/*; \
    rm -f /etc/systemd/system/*.wants/*; \
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*; \
    rm -f /lib/systemd/system/anaconda.target.wants/*; \
    rm -f /lib/systemd/system/plymouth*; \
    rm -f /lib/systemd/system/systemd-update-utmp*

# copy system stuff
COPY assets/system/ /

# enable aavm service
RUN systemctl enable aavm.service

# copy components
COPY assets/components "${AAVM_DIR}/components/available"

# install components
# - Docker
#RUN aavm-component-install docker
#LABEL aavm.environment.components.docker="1"

# - Docker Compose
#RUN aavm-component-install docker-compose
#LABEL aavm.environment.components.docker-compose="1"

# - Docker Rootless
#RUN aavm-component-install docker-rootless
#LABEL aavm.environment.components.docker-rootless="1"

# - SSH Server
#RUN aavm-component-install openssh-server
#LABEL aavm.environment.components.openssh-server="1"

# - mDNS and zeroconf support
#RUN aavm-component-install avahi
#LABEL aavm.environment.components.avahi="1"

# set the stop signal to use against systemd
STOPSIGNAL SIGRTMIN+3

# store aavm metadata
LABEL \
    aavm.runtime="1" \
    aavm.environment.os_family="linux" \
    aavm.environment.arch="${ARCH}" \
    aavm.environment.description="${DESCRIPTION}" \
    aavm.environment.maintainer="${MAINTAINER}"
