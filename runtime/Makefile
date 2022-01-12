EXTRA_ARGS=


build-all:
	cpk build -C ./ubuntu20.04 -a amd64 ${EXTRA_ARGS}
	cpk build -C ./ubuntu20.04 -a arm64v8 ${EXTRA_ARGS}

	cpk build -C ./sshd8.2 -a amd64 ${EXTRA_ARGS}
	cpk build -C ./sshd8.2 -a arm64v8 ${EXTRA_ARGS}

	cpk build -C ./docker20.10.7 -a amd64 ${EXTRA_ARGS}
	cpk build -C ./docker20.10.7 -a arm64v8 ${EXTRA_ARGS}

	cpk build -C ./rootless-docker20.10.7 -a amd64 ${EXTRA_ARGS}
	cpk build -C ./rootless-docker20.10.7 -a arm64v8 ${EXTRA_ARGS}


release-all:
	$(MAKE) build-all EXTRA_ARGS="--push"
