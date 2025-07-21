cmake_minimum_required(VERSION 3.10)
project(ProcessMonitorClient)

set(CMAKE_CXX_STANDARD 17)

find_package(Boost REQUIRED COMPONENTS system)

# Build executable
add_executable(client
    main.cpp
    tcp_client.cpp
    process.cpp
)

target_link_libraries(client PRIVATE Boost::system pthread)
