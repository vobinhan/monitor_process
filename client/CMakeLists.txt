cmake_minimum_required(VERSION 3.10)
project(ProcessMonitorClient)

set(CMAKE_CXX_STANDARD 17)

# Tìm thư viện Boost (cho TCP)
find_package(Boost REQUIRED COMPONENTS system)

# Build executable
add_executable(client
    main.cpp
    tcp_client.cpp
    process.cpp
)

# Liên kết thư viện Boost
target_link_libraries(client PRIVATE Boost::system)
