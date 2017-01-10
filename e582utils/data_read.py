"""
  download a file named filename from the atsc301 downloads directory
  and save it as a local file with the same name.

  command line example::

    python -m a301utils.a301_readfile photon_data.csv

  module example::

    from a301utils.a301_readfile import download
    download('photon_data.csv')

"""
import argparse
import requests
from pathlib import Path
import sys
import os
import shutil

def download(filename):
    """
    copy file filename from http://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads to 
    the local directory

    
    Parameters
    ----------

    filename: string
      name of file to fetch from 

    Returns
    -------

    Side effect: Creates a copy of that file in the local directory
    """
    url = 'https://clouds.eos.ubc.ca/~phil/courses/atsc301/downloads/{}'.format(filename)
    filepath = Path('./{}'.format(filename))
    if filepath.exists():
        the_size = filepath.stat().st_size
        print(('\n{} already exists\n'
               'and is {} bytes\n'
               'will not overwrite\n').format(filename,the_size))
        return None

    tempfile = str(filepath) + '_tmp'
    temppath = Path(tempfile)
    with open(tempfile, 'wb') as localfile:
        response = requests.get(url, stream=True)

        if not response.ok:
            print('response: ',response)
            raise Exception('Something is wrong, requests.get() failed with filename {}'.format(filename))

        for block in response.iter_content(1024):
            if not block:
                break

            localfile.write(block)
            
    the_size=temppath.stat().st_size
    if the_size < 10.e3:
        print('Warning -- your file is tiny (smaller than 10 Kbyte)\nDid something go wrong?')
    shutil.move(tempfile,filename)
    the_size=filepath.stat().st_size
    print('downloaded {}\nsize = {}'.format(filename,the_size))
    return None


if __name__ == "__main__":

    linebreaks=argparse.RawTextHelpFormatter
    descrip=__doc__.lstrip()
    parser = argparse.ArgumentParser(formatter_class=linebreaks,description=descrip)
    parser.add_argument('filename',type=str,help='name of file to download')
    args=parser.parse_args()
    download(args.filename)
   
    


