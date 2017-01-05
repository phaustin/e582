To reinstall conda from scratch with the A405 packages:

1. Go to http://conda.pydata.org/miniconda.html and download the Python 3.5 version

2. Install into a new, non-existing directory (conda will create it), for example
   mini35_test

3. Make sure this version of miniconda is at the front of your path.  In a windows
   cmd shell, type

   ``` 
   where conda
   ```

   and make sure that you are getting mini35_test/Scripts/conda

   For osx/linux bash shells, the command is

   ``` 
   which conda
   ```
   
   and conda should be in mini35_test/bin/conda

4. In the shell, cd to  the folder containing this readme, then do 
   
   ```
   conda install --file class_specs.txt
   ```

   to get the packages

5. The following packages are not available from conda -- use pip:
   
   ```
   pip install ruamel.yaml
   pip install tzlocal
   ```
   
6. To get a list of packages that you've installed using conda and pip
   cd to the folder containing this readme and do:
   
   ```
   python split_conda.py
   ```
   
   which will produce the following four files:
 
   ```bash
   all_packages.txt (raw output)
   all_packages.txt_err (error messages if any)
   conda_specs.txt  (conda installed packages)
   pip_specs.txt (pip installed packages)
   ```
