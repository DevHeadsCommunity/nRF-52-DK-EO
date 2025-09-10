# EmbedOps

## Problems encountered setting up the project
The build fails when running `eo build` after noticeably Zephyr has completed
installation.

** What have I done **
```
eo login # success
eo init
eo add embedops-devkit # chose c
eo build #fails
```

```sh
-- west build: generating a build system
CMake Warning at CMakeLists.txt:6 (find_package):
  By not providing "Findzephyr.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "zephyr", but
  CMake did not find one.

  Could not find a package configuration file provided by "zephyr" with any
  of the following names:

    zephyrConfig.cmake
    zephyr-config.cmake

  Add the installation prefix of "zephyr" to CMAKE_PREFIX_PATH or set
  "zephyr_DIR" to a directory containing one of the above files.  If "zephyr"
  provides a separate development package or SDK, be sure it has been
  installed.


-- The C compiler identification is unknown
-- The CXX compiler identification is unknown
CMake Error at CMakeLists.txt:7 (project):
  No CMAKE_C_COMPILER could be found.

  Tell CMake where to find the compiler by setting either the environment
  variable "CC" or the CMake cache entry CMAKE_C_COMPILER to the full path to
  the compiler, or to the compiler name if it is in the PATH.


CMake Error at CMakeLists.txt:7 (project):
  No CMAKE_CXX_COMPILER could be found.

  Tell CMake where to find the compiler by setting either the environment
  variable "CXX" or the CMake cache entry CMAKE_CXX_COMPILER to the full path
  to the compiler, or to the compiler name if it is in the PATH.


-- Configuring incomplete, errors occurred!
FATAL ERROR: command exited with status 1: /usr/bin/cmake -DWEST_PYTHON=/opt/zephyrproject/.venv/bin/python3 -B/workspaces/nRF-52-DK-EO/app/build -GNinja -DBOARD=embedops/stm32f0-devkit -S/workspaces/nRF-52-DK-EO/app
-- west build: generating a build system
CMake Warning at CMakeLists.txt:6 (find_package):
  By not providing "Findzephyr.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "zephyr", but
  CMake did not find one.

  Could not find a package configuration file provided by "zephyr" with any
  of the following names:

    zephyrConfig.cmake
    zephyr-config.cmake

  Add the installation prefix of "zephyr" to CMAKE_PREFIX_PATH or set
  "zephyr_DIR" to a directory containing one of the above files.  If "zephyr"
  provides a separate development package or SDK, be sure it has been
  installed.


-- The C compiler identification is unknown
-- The CXX compiler identification is unknown
CMake Error at CMakeLists.txt:7 (project):
  No CMAKE_C_COMPILER could be found.

  Tell CMake where to find the compiler by setting either the environment
  variable "CC" or the CMake cache entry CMAKE_C_COMPILER to the full path to
  the compiler, or to the compiler name if it is in the PATH.


CMake Error at CMakeLists.txt:7 (project):
  No CMAKE_CXX_COMPILER could be found.

  Tell CMake where to find the compiler by setting either the environment
  variable "CXX" or the CMake cache entry CMAKE_CXX_COMPILER to the full path
  to the compiler, or to the compiler name if it is in the PATH.


-- Configuring incomplete, errors occurred!
FATAL ERROR: command exited with status 1: /usr/bin/cmake -DWEST_PYTHON=/opt/zephyrproject/.venv/bin/python3 -B/workspaces/nRF-52-DK-EO/app/build -GNinja -DBOARD=embedops/stm32f0-devkit -S/workspaces/nRF-52-DK-EO/app
Error: exit status 1
Usage:
  eo build [flags]

Flags:
  -h, --help   help for build
```

I have tried to add `arm-none-build-gcc`, `zephyr` then retried the build but nothing works.

** Environment **
Linux fedora 6.16.5-100.fc41.x86_64
Nodejs v24.7.0
embedops: 3.1.1
