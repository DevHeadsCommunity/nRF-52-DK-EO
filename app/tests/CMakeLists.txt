cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

set(BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_PREFIX_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../zephyr)

project(nrf52dk_eo_tests)

FILE(GLOB app_sources src/*.c)

FILE(GLOB conv_sources ../src/conversions.c)

include_directories(../src)

target_sources(app PRIVATE ${app_sources} ${conv_sources})
