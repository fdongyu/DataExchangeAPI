# Compiler
FC = gfortran
CC = gcc

# Compiler flags
FFLAGS = -c
CFLAGS = -c

# Libraries
LIBS = -lcurl

# Source files
FORTRAN_SOURCES = data_exchange.f90 http_interface.f90 e3sm_test.f90
C_SOURCES = http_impl.c

# Object files
FORTRAN_OBJECTS = $(FORTRAN_SOURCES:.f90=.o)
C_OBJECTS = $(C_SOURCES:.c=.o)

# Executable
EXECUTABLE = data_exchange

# Targets
all: $(EXECUTABLE)

$(EXECUTABLE): $(FORTRAN_OBJECTS) $(C_OBJECTS)
	$(FC) -o $@ $^ $(LIBS)

%.o: %.f90
	$(FC) $(FFLAGS) -o $@ $<

%.o: %.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(EXECUTABLE) $(FORTRAN_OBJECTS) $(C_OBJECTS) *.mod
