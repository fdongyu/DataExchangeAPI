
# Add the executable
add_executable(e3sm_test1 ${CMAKE_CURRENT_SOURCE_DIR}/e3sm/e3sm_test1.f90)
target_include_directories(e3sm_test1 PUBLIC ${PROJECT_SOURCE_DIR}/src/clients/e3sm)
target_link_libraries(e3sm_test1 PUBLIC e3sm)

add_executable(e3sm_test2 ${CMAKE_CURRENT_SOURCE_DIR}/e3sm/e3sm_test2.f90)
target_include_directories(e3sm_test2 PUBLIC ${PROJECT_SOURCE_DIR}/src/clients/e3sm)
target_link_libraries(e3sm_test2 PUBLIC e3sm)

add_executable(e3sm_test3 ${CMAKE_CURRENT_SOURCE_DIR}/e3sm/e3sm_test3.f90)
target_include_directories(e3sm_test3 PUBLIC ${PROJECT_SOURCE_DIR}/src/clients/e3sm)
target_link_libraries(e3sm_test3 PUBLIC e3sm)
