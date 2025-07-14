# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/root/monitor_process/client/build/_deps/cxxopts-src"
  "/root/monitor_process/client/build/_deps/cxxopts-build"
  "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix"
  "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/tmp"
  "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/src/cxxopts-populate-stamp"
  "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/src"
  "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/src/cxxopts-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/src/cxxopts-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/root/monitor_process/client/build/_deps/cxxopts-subbuild/cxxopts-populate-prefix/src/cxxopts-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
