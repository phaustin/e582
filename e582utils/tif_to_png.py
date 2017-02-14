'''
convert tif file to png

example:  

   python -m e582utils.tif_to_png stretched_rgb.tif

will produce the file stretched_rgb.png

requires the pillow module:
conda install pillow
'''
from PIL import Image
import argparse
from pathlib import Path

if __name__=="__main__":
    linebreaks=argparse.RawTextHelpFormatter
    descrip=__doc__.lstrip()
    parser = argparse.ArgumentParser(formatter_class=linebreaks,description=descrip)
    parser.add_argument('tif_file',type=str,help='input tif to convert')
    args=parser.parse_args()
    infile = Path(args.tif_file)
    outfile = infile.with_suffix('.png')
    with Image.open(str(infile)) as im:
        im.save(outfile)
    print('converted {} to {}'.format(str(infile),str(outfile)))

