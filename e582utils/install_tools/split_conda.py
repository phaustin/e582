#!/usr/bin/env python
"""
  usage:  python split_conda.py

  output:  4 text files

    all_packages.txt (raw output)
    all_packages.txt_err (error messages if any)
    conda_specs.txt  (conda installed packages)
    pip_specs.txt (pip installed packages)
"""
import subprocess,shlex

outfile="all_packages.txt"
command = "conda list"
with open(outfile,'w') as stdout:
    with open(outfile + '_err','w') as stderr:
        subprocess.check_call(shlex.split(command),stderr=stderr,stdout=stdout)

with open(outfile,'r') as f:
    lines=f.readlines()

with open('conda_specs.txt','w') as fconda:
    with open('pip_specs.txt','w') as fpip:
        for line in lines:
            if line.find('<pip>') > -1:
                fout = fpip
            else:
                fout = fconda
            try:
                vals=line.split()
                fout.write('{}\n'.format(vals[0]))
            except ValueError:
                print(line)
                pass
        
    
    

