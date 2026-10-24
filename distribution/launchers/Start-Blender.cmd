@echo off
setlocal
set "OCIO=%~dp03.6\datafiles\colormanagement\config.ocio"
"%~dp0blender.exe" %*
exit /b %errorlevel%
