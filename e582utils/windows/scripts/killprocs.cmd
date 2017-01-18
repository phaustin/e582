@rem -- call a long python module with a short cmd script
@rem -- %* passes all arguments after the command name to the
@rem -- python script
@example:  killprocs mini3
@will run  python -m e582utils.killprocs mini3
@echo off
python -m e582utils.killprocs %*

