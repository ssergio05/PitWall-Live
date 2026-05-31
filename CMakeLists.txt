cmake_minimum_required(VERSION 3.10)
project(F1TelemetryLink)
set(CMAKE_CXX_STANDARD 20)

find_package(Threads REQUIRED)

add_executable(f1_receiver 
    src/main.cpp 
    src/Receiver.cpp
    src/Logger.cpp
)

target_link_libraries(f1_receiver Threads::Threads ws2_32)