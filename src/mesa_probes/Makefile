# Out-of-tree build of mesa_probe against an existing MESA installation.
# Requires MESA_DIR and an initialized mesasdk environment (see build.sh).

MESA_DIR ?= $(HOME)/mesa-r23.05.1

include $(MESA_DIR)/utils/makefile_header

MESA_LIB_DIR = $(MESA_DIR)/lib
MESA_INCLUDE_DIR = $(MESA_DIR)/include
WORK_SRC_DIR = .

LOAD_OTHER = -L$(MESA_LIB_DIR) -lnet -leos -lrates -lchem $(LOAD_MESA_NUMERICS)

mesa_probe : probe.o
	$(LOADER) $(FCopenmp) -o $@ probe.o $(LOAD_OTHER) $(LD_FLAGS)

probe.o : probe.f90
	$(TEST_COMPILE) $(FCfree) probe.f90

clean :
	rm -f mesa_probe *.o *.mod
