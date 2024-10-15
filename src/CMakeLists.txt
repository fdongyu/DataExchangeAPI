

add_fortran_library(e3sm
                    clients/e3sm/high_level_api.f90 
                    clients/e3sm/low_level_fortran_interface.f90 
                    clients/e3sm/low_level_c_api.c
                    )
target_link_libraries(e3sm PUBLIC CURL::libcurl)
target_compile_features(e3sm PUBLIC)