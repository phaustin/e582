#!/usr/bin/env python
"""
kill all processes containing a string

example: python -m e582utils.killprocs mini3

will kill all process with mini3 in the name

requires this module
https://pythonhosted.org/psutil/
"""
import psutil
from e582utils.helper_funs import make_tuple

import argparse
import textwrap


def on_terminate(proc):
    print("process {} terminated with exit code {}".format(
               proc, proc.returncode))

def killit(snip):
    """
    kill all processs with names containing the string snip

    Parameters
    ----------

    snip: str
      process name string to search for

    Returns
    -------

    kills processes as side effect
    """
    keepit = {}
    keys = ['time', 'name', 'cmdline', 'proc']
    for proc in psutil.process_iter():
        try:
            the_dict = dict(zip(keys, (proc.create_time(), proc.exe(),
                                       proc.cmdline(), proc)))
            keepit[proc.pid] = make_tuple(the_dict)
        except (psutil.ZombieProcess, psutil.AccessDenied,
                psutil.NoSuchProcess):
            pass
    print('in killprocs.py, looking for {}'.format(snip))
    #
    # don't kill this process or the emacs python parser
    #
    proclist = []
    for the_tup in keepit.values():
        string_cmd = ' '.join(the_tup.cmdline)
        if the_tup.name.find(args.snip) > -1 and \
           string_cmd.find('killprocs') == -1 and \
           string_cmd.find('elpy') == -1:
            proclist.append(the_tup)

    proconly = [item.proc for item in proclist]
    for item in proconly:
        cmd_string = ' '.join(item.cmdline())
        print('terminating: {}'.format(cmd_string))
    [proc.terminate() for proc in proconly]

    gone, alive = psutil.wait_procs(proconly, timeout=3, callback=on_terminate)

    for p in alive:
        p.kill()

def make_parser():
    """
    set up the command line arguments needed to call the program
    """
    linebreaks = argparse.RawTextHelpFormatter
    parser = argparse.ArgumentParser(
        formatter_class=linebreaks, description=__doc__.lstrip())
    parser.add_argument('snip', type=str, help='string in processname')
    return parser
    

if __name__ == "__main__":

    parser = make_parser()
    args = parser.parse_args()
    killit(args.snip)

        
