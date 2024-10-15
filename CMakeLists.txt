
cmake_minimum_required(VERSION 3.0)
project(DataExchangeServer LANGUAGES C Fortran) # C and fortran 

# Required for e3sm C code
find_package(CURL REQUIRED)
include_directories(${CURL_INCLUDE_DIR})


# Function to make fortran modules easy to link
# Source: https://stackoverflow.com/questions/54549959/how-to-fix-cmake-fortran-modules-dependency
function(add_fortran_library LIB)
    add_library(${LIB} ${ARGN})

    # set module path to LIB_DIR/mod
    get_target_property(LIB_DIR ${LIB} BINARY_DIR)
    set_target_properties(${LIB} PROPERTIES Fortran_MODULE_DIRECTORY ${LIB_DIR}/mod)

    # making LIB_DIR/mod available for libraries linking LIB 
    target_include_directories(${LIB} INTERFACE ${LIB_DIR}/mod)
endfunction(add_fortran_library)

# Source
add_subdirectory(src)

# Tests
add_subdirectory(tests)

# Documentation
# add_subdirectory(doc)
 
