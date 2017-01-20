@rem !!! Do not change this file in-place, change its copy instead !!!
@rem !!!  Otherwise you will lose your settings after next update  !!!

@echo off

rem Simple "ver" prints empty line before Windows version
rem Use this construction to print just a version info
cmd /d /c ver | "%windir%\system32\find.exe" "Windows"

rem Now we form the command prompt

rem This will start prompt with `User@PC `
set ConEmuPrompt0=$E[m$E[32m$E]9;8;"USERNAME"$E\@$E]9;8;"COMPUTERNAME"$E\$S

rem Followed by colored `Path`
set ConEmuPrompt1=%ConEmuPrompt0%$E[92m$P$E[90m
if NOT "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
  if "%PROCESSOR_ARCHITEW6432%" == "AMD64" if "%PROCESSOR_ARCHITECTURE%" == "x86" (
    rem Use another text color if cmd was run from SysWow64
    set ConEmuPrompt1=%ConEmuPrompt0%$E[93m$P$E[90m
  )
)

rem Carriage return and `$` or `>`
rem Spare `$E[90m` was specially added because of GitShowBranch.cmd
if "%ConEmuIsAdmin%" == "ADMIN" (
  set ConEmuPrompt2=$_$E[90m$$
) else (
  set ConEmuPrompt2=$_$E[90m$G
)

rem Finally reset color and add space
set ConEmuPrompt3=$E[m$S$E]9;12$E\
if /I "%~1" == "/git" goto git
if /I "%~1" == "-git" goto git
goto no_git

:git
call "%~dp0GitShowBranch.cmd" /i
goto :EOF

:no_git
rem Set new prompt
PROMPT %ConEmuPrompt1%%ConEmuPrompt2%%ConEmuPrompt3%
rem this is a simpler black and white choice
PROMPT $P$Gcmd$_$G$S
set E582MASTER=%USERPROFILE%\repos\pythonlibs
set HOME=%USERPROFILE%
set PATH=%E582MASTER%\e582utils\windows\scripts;C:\Program Files\Docker\Docker\Resources\bin;c:\msys64\usr\bin;c:\Program Files/HDF_Group/H4TOH5/2.2.2/bin;c:/Program Files (x86)/Microsoft VS Code/bin;%PATH%
set PYTHONPATH=%E582MASTER%
set PWD=%~dp0
set ecode=%USERPROFILE%\repos\e582_2016
set h=%USERPROFILE%
@echo running %~dp0CmdInit.cmd
rem to run this from conemu set the conemu cmd task
rem to: cmd.exe /k "%UserProfile%\repos\pythonlibs\e582utils\install_tools\shell_rcfiles\CmdInit.cmd"

