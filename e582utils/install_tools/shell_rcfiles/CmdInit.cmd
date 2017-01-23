@rem  original CmdInit.cmd file is installed at
@rem c:/Program Files/ConEmu/ConEmu/CmdInit.cmd
@rem to see prompt customization codes, do
@rem prompt /?
@echo off
rem this is a simple black and white prompt choice
PROMPT $P$Gcmd$_$G$S
set E582MASTER=%USERPROFILE%\repos\pythonlibs
set HOME=%USERPROFILE%
set PYTHONPATH=%E582MASTER%
rem
rem comment out or delete any path folders you don't need
rem
set PATH=%E582MASTER%\e582utils\windows\scripts;%PATH%
set PATH=c:\msys64\usr\bin;%PATH%
set PATH=C:\Program Files\Docker\Docker\Resources\bin;%PATH%
set PATH=c:\Program Files/HDF_Group/H4TOH5/2.2.2/bin;%PATH%
set PWD=%~dp0
set ecode=%USERPROFILE%\repos\e582_2016
set h=%USERPROFILE%
@echo running %~dp0CmdInit.cmd
rem to run this when a shell starts from conemu set the conemu cmd task
rem to: cmd.exe /k "%UserProfile%\repos\pythonlibs\e582utils\install_tools\shell_rcfiles\CmdInit.cmd"

