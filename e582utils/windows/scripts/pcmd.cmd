@echo off
rem
rem  if pcmd.cmd is in a folder in %PATH% this will read in
rem  the cmd rcfile and cd to your home directory
rem
cmd.exe /k "%UserProfile%\repos\pythonlibs\e582utils\install_tools\shell_rcfiles\CmdInit.cmd && cd %USERPROFILE%"
