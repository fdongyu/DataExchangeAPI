# Compiler
FC = gfortran
CC = gcc

# Compiler flags
FFLAGS = -c
CFLAGS = -c

# Libraries
LIBS = -lcurl

# Directory
LIB_DIR = data_exchange_lib/

# Source files
FORTRAN_SOURCES = $(LIB_DIR)http_interface.f90 e3sm_test.f90
C_SOURCES = $(LIB_DIR)http_impl.c

# Object files
FORTRAN_OBJECTS = $(FORTRAN_SOURCES:.f90=.o)
C_OBJECTS = $(C_SOURCES:.c=.o)

# Executable name
EXECUTABLE = e3sm_test

# Targets
all: $(EXECUTABLE)

$(EXECUTABLE): $(FORTRAN_OBJECTS) $(C_OBJECTS)
	$(FC) -o $@ $^ $(LIBS)

%.o: %.f90
	$(FC) $(FFLAGS) $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f $(EXECUTABLE) $(FORTRAN_OBJECTS) $(C_OBJECTS) $(LIB_DIR)*.mod

.PHONY: all clean
