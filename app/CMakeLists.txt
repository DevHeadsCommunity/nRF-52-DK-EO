cmake_minimum_required(VERSION 3.20.0)

set(KCONFIG_ERROR_ON_WARNINGS OFF)

FILE(GLOB app_sources csrc/*.c)


set(BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR}) 
set(CMAKE_PREFIX_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../zephyr)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app C)
target_sources(app PRIVATE ${app_sources})
