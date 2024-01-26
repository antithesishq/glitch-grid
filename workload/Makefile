ifeq ($(shell command -v podman 2> /dev/null),)
    CMD=docker
else
    CMD=podman
endif

GIT_HASH ?= $(shell git log --format="%h" -n 1)
_BUILD_ARGS_TAG ?= ${GIT_HASH}
_BUILD_ARGS_RELEASE_TAG ?= latest
_BUILD_ARGS_DOCKERFILE ?= Dockerfile
_BUILD_ARGS_APPLICATION ?= __does_not_exist__

all: all_build

all_build: build_workload

.PHONY: all

_builder:
	$(CMD) build --tag demo-${_BUILD_ARGS_APPLICATION}:${_BUILD_ARGS_TAG} -f ${_BUILD_ARGS_DOCKERFILE} .
 
_pusher:
	$(CMD) push demo-${_BUILD_ARGS_APPLICATION}:${_BUILD_ARGS_TAG}
 
_releaser:
	$(CMD) pull demo-${_BUILD_ARGS_APPLICATION}:${_BUILD_ARGS_TAG}
	$(CMD) tag  demo-${_BUILD_ARGS_APPLICATION}:${_BUILD_ARGS_TAG} ${APPLICATION_NAME}:latest
	$(CMD) push demo-${_BUILD_ARGS_APPLICATION}:${_BUILD_ARGS_RELEASE_TAG}

build_%:
	$(MAKE) _builder \
		-e _BUILD_ARGS_TAG="$*-${GIT_HASH}" \
		-e _BUILD_ARGS_DOCKERFILE="Dockerfile.$*" \
		-e _BUILD_ARGS_APPLICATION="$*"
 
push_%:
	$(MAKE) _pusher -e _BUILD_ARGS_TAG="$*-${GIT_HASH}"
 
release_%:
	$(MAKE) _releaser \
		-e _BUILD_ARGS_TAG="$*-${GIT_HASH}" \
		-e _BUILD_ARGS_RELEASE_TAG="$*-latest"
