@echo off
@echo "running bashrc.cmd"
set HOME=%HOMEDRIVE%\%HOMEPATH%
set PATH=c:\msys64\usr\bin;%PATH%
set PYTHONPATH=%HOME%\repos\pythonlibs
set PWD=%~dp0
