# Compiler
FC = gfortran
CC = gcc

# Compiler flags
FFLAGS = -c -J$(OBJ_DIR)
CFLAGS = -c

# Libraries
LIBS = -lcurl

# Directories
SRC_DIR = ../../../src/clients/e3sm/lib/
OBJ_DIR = ./obj/

# Source files
FORTRAN_SOURCES = $(SRC_DIR)low_level_fortran_api.f90 $(SRC_DIR)high_level_api.f90
C_SOURCES = $(SRC_DIR)low_level_c_api.c
TEST_SOURCES = e3sm_test.f90

# Object files
FORTRAN_OBJECTS = $(patsubst %.f90,$(OBJ_DIR)%.o,$(notdir $(FORTRAN_SOURCES)))
C_OBJECTS = $(patsubst %.c,$(OBJ_DIR)%.o,$(notdir $(C_SOURCES)))
TEST_OBJECTS = $(patsubst %.f90,$(OBJ_DIR)%.o,$(notdir $(TEST_SOURCES)))

# Executable name
EXECUTABLE = e3sm_test

# Default target
all: $(EXECUTABLE)

# Linking the executable
$(EXECUTABLE): $(FORTRAN_OBJECTS) $(C_OBJECTS) $(TEST_OBJECTS)
	$(FC) -o $@ $^ $(LIBS)

# Compiling Fortran source files
$(OBJ_DIR)%.o: $(SRC_DIR)%.f90
	$(FC) $(FFLAGS) $< -o $@

# Compiling C source files
$(OBJ_DIR)%.o: $(SRC_DIR)%.c
	$(CC) $(CFLAGS) $< -o $@

# Compiling Fortran test files
$(OBJ_DIR)%.o: %.f90
	$(FC) $(FFLAGS) $< -o $@

# Cleaning up
clean:
	rm -f $(EXECUTABLE) $(OBJ_DIR)*.o $(OBJ_DIR)*.mod

# Phony targets
.PHONY: all clean
