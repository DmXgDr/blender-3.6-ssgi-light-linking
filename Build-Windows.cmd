@echo off
setlocal
if "%~1"=="" (
  echo Usage: Build-Windows.cmd dependency-directory [output-directory]
  echo Run from an x64 Native Tools command prompt for Visual Studio 2022.
  exit /b 1
)
where cl.exe >nul 2>nul
if errorlevel 1 exit /b 2
set "LIBRARY_DIR=%~f1"
set "OUTPUT_DIR=%~dp0build-output"
if not "%~2"=="" set "OUTPUT_DIR=%~f2"
set "_CL_=%_CL_% /wd5287"
cmake -S "%~dp0blender" -B "%OUTPUT_DIR%\build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PROJECT_INCLUDE="%~dp0tools\Release-Options.cmake" -DCMAKE_INSTALL_PREFIX="%OUTPUT_DIR%\app" -DLIBDIR="%LIBRARY_DIR%" -DWITH_CYCLES=OFF -DWITH_GTESTS=OFF -DWITH_BLENDER_THUMBNAILER=OFF -DWITH_COMPILER_ASAN=OFF -DWITH_WINDOWS_BUNDLE_CRT=ON -DWITH_BUILDINFO=ON
if errorlevel 1 exit /b 3
cmake --build "%OUTPUT_DIR%\build" --parallel 8
if errorlevel 1 exit /b 4
cmake --install "%OUTPUT_DIR%\build"
exit /b %errorlevel%
