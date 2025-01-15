# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(peripheral_dis)

target_sources(app PRIVATE
  src/main.c
  src/ble.c
  src/cli.c
  src/util.c
  src/serial.c
)

include_directories(src)

zephyr_library_include_directories(${ZEPHYR_BASE}/samples/bluetooth)

# Print out all variables to see what we can use from zephyr subdir
# turns out the following are useful:
#   __build_dir -> the build/zephyr dir
#   app_PM_TARGET -> the zephyr.elf target
#   KERNEL_ELF_NAME -> zehpyr.elf string
# message(STATUS "-------------------------------------------------------")
# get_cmake_property(_variableNames VARIABLES)
# list (SORT _variableNames)
# foreach (_variableName ${_variableNames})
#     message(STATUS "${_variableName}=${${_variableName}}")
# endforeach()

# ease of use veriable for target filename
set(elf_size_file ${KERNEL_ELF_NAME}.size)

# Add a command that calls the appropriate size command and depends on the zephyr.elf contained in app_PM_TARGET
add_custom_command(OUTPUT ${__build_dir}/${elf_size_file} COMMAND ${_CMAKE_TOOLCHAIN_LOCATION}/${_CMAKE_TOOLCHAIN_PREFIX}size --format=berkeley ${__build_dir}/${KERNEL_ELF_NAME} | tee ${__build_dir}/${elf_size_file}  DEPENDS ${app_PM_TARGET} )

# Custom POSTBUILD commands can't target a subdirectory target directly so create a custom target that depends on the file generated in the custom command
# see https://stackoverflow.com/questions/40294146/alternative-to-cmake-post-build-command-when-target-is-in-subdirectory
add_custom_target(elf_size ALL
    DEPENDS ${__build_dir}/${elf_size_file}
)
