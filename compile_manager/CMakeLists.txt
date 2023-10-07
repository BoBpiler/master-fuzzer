cmake_minimum_required(VERSION 3.22)
project(compile_manager)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory("pipe_manager")
add_executable(${PROJECT_NAME} "compile_manager.cpp")

target_link_libraries(${PROJECT_NAME}
	PUBLIC
    	pipe_manager
)
#endif()

# Set Test Mode Option
#option(TEST_CODE "Build with test code" OFF)

#if(TEST_CODE)
#    add_subdirectory("test_code")
#	add_subdirectory("src")
#endif()