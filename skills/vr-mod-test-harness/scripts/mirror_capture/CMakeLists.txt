# Builds openvr_mirror_capture (Windows, MSVC, D3D11). OPENVR_SDK_DIR is a checkout or release of
# https://github.com/ValveSoftware/openvr (headers/, lib/win64/, bin/win64/).
#
#   cmake -S . -B build -DOPENVR_SDK_DIR=C:/path/to/openvr
#   cmake --build build --config Release
cmake_minimum_required(VERSION 3.20)
project(openvr_mirror_capture CXX)

set(OPENVR_SDK_DIR "" CACHE PATH "OpenVR SDK folder (holds headers/ and lib/win64/)")
set(OPENVR_DLL "${OPENVR_SDK_DIR}/bin/win64/openvr_api.dll" CACHE FILEPATH "openvr_api.dll copied next to the exe")
if(NOT EXISTS "${OPENVR_SDK_DIR}/headers/openvr.h")
  message(FATAL_ERROR "Set OPENVR_SDK_DIR to the OpenVR SDK (no headers/openvr.h in '${OPENVR_SDK_DIR}')")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(openvr_mirror_capture openvr_mirror_capture.cpp)
target_include_directories(openvr_mirror_capture PRIVATE "${OPENVR_SDK_DIR}/headers")
target_link_libraries(openvr_mirror_capture PRIVATE "${OPENVR_SDK_DIR}/lib/win64/openvr_api.lib" d3d11 dxgi)
target_compile_definitions(openvr_mirror_capture PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
add_custom_command(TARGET openvr_mirror_capture POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different "${OPENVR_DLL}" "$<TARGET_FILE_DIR:openvr_mirror_capture>")
