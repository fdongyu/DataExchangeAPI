# Compiler
FC = gfortran
CC = gcc

# Compiler flags
FFLAGS = -c
CFLAGS = -c

# Libraries
LIBS = -lcurl

# Directories
SRC_DIR = ../../../src/clients/e3sm/lib/

# Source files
FORTRAN_SOURCES = $(SRC_DIR)low_level_fortran_interface.f90 $(SRC_DIR)high_level_api.f90
C_SOURCES = $(SRC_DIR)low_level_c_api.c
TEST_SOURCES = e3sm_test.f90

# Object files
FORTRAN_OBJECTS = $(patsubst %.f90,%.o,$(notdir $(FORTRAN_SOURCES)))
C_OBJECTS = $(patsubst %.c,%.o,$(notdir $(C_SOURCES)))
TEST_OBJECTS = $(patsubst %.f90,%.o,$(notdir $(TEST_SOURCES)))

# Executable name
EXECUTABLE = e3sm_test

# Default target
all: $(EXECUTABLE)

# Linking the executable
$(EXECUTABLE): $(FORTRAN_OBJECTS) $(C_OBJECTS) $(TEST_OBJECTS)
	$(FC) -o $@ $^ $(LIBS)

# Compiling Fortran source files
%.o: $(SRC_DIR)%.f90
	$(FC) $(FFLAGS) $< -o $@

# Compiling C source files
%.o: $(SRC_DIR)%.c
	$(CC) $(CFLAGS) $< -o $@

# Compiling Fortran test files
%.o: %.f90
	$(FC) $(FFLAGS) $< -o $@

# Cleaning up
clean:
	rm -f $(EXECUTABLE) *.o *.mod

# Phony targets
.PHONY: all clean
