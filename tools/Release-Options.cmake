# Use the redistributable directory from the developer command prompt.
if(DEFINED ENV{VCToolsRedistDir})
  file(TO_CMAKE_PATH "$ENV{VCToolsRedistDir}" MSVC_REDIST_DIR)
endif()
# Optional override if CMake cannot recognize localized /showIncludes output.
if(DEFINED ENV{BLENDER_MSVC_INCLUDE_PREFIX})
  set(CMAKE_CL_SHOWINCLUDES_PREFIX "$ENV{BLENDER_MSVC_INCLUDE_PREFIX}")
endif()
