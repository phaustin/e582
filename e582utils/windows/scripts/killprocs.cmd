@rem -- call a long python module with a short cmd script
@rem -- %* passes all arguments after the command name to the
@rem -- python script
@rem example:  killprocs mini3
@rem will run  python -m e582utils.killprocs mini3
@echo off
python -m e582utils.killprocs %*

