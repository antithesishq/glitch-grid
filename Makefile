# Top-level makefile. Go into each subdirectory and run make
# SUBDIRS := $(wildcard system_under_test/*/.)

SUBDIRS := ./control/ ./vault/ ./workload/

all: $(SUBDIRS)
$(SUBDIRS):
	$(MAKE) -C $@

.PHONY: all $(SUBDIRS)
