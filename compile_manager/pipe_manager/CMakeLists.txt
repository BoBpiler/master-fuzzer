project(pipe_manager)
add_library(pipe_manager pipe_manager.cpp)

#target_link_libraries(pipe_manager
#    PUBLIC
#        ${mygmpxx}
#        ${mygmp}
#)
set_target_properties(pipe_manager PROPERTIES PUBLIC_HEADER pipe_manager.h)

# specify the include directory for the library
target_include_directories(pipe_manager PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_options(pipe_manager PRIVATE -fPIC)