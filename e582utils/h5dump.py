#!/usr/bin/env python
"""
Dump groups, datasets and attributes for an hdf5 file

to run from anywhere:  python -m a301utils.h5dump h5_file

"""
import h5py
import argparse
import sys


def print_attrs(name, obj):
    if obj.parent.name == '/':
        print('_' * 15)
        print('root group object', repr(obj))
        print('_' * 15)
    else:
        print('member of group: ', obj.parent.name, obj)
    try:
        for key, val in obj.attrs.items():
            print("    %s: %s" % (key, val))
    except IOError:
        print('this is an HDFStore pandas dataframe')
        print(name, obj)
        print('-' * 20)


def dumph5(filename):
    #
    # make sure that have a filename, not an open file
    #
    if isinstance(filename, h5py._hl.files.File):
        raise Exception('need simple filename')
    with h5py.File(filename, 'r') as infile:
        print('+' * 20)
        print('found the following top-level items: ')
        for name, object in infile.items():
            print('{}: {}'.format(name, object))
        print('+' * 20)
        infile.visititems(print_attrs)
        print('-------------------')
        print("attributes for the root file")
        print('-------------------')
        try:
            for key, value in infile.attrs.items():
                print("attribute name: ", key, "--- value: ", value)
        except IOError:
            pass
    return None


def make_parser():
    """
    set up the command line arguments needed to call the program
    """
    linebreaks = argparse.RawTextHelpFormatter
    parser = argparse.ArgumentParser(
        formatter_class=linebreaks, description=__doc__.lstrip())
    parser.add_argument('h5_file', type=str, help='name of h5 file')
    return parser


def main(args=None):
    """
    args: optional -- if missing then args will be taken from command line
          or pass [h5_file] -- list with name of h5_file to open
    """
    parser = make_parser()
    args = parser.parse_args(args)
    filename = args.h5_file
    dumph5(filename)


if __name__ == "__main__":
    #
    # will exit with non-zero return value if exceptions occur
    #
    #args = ['vancouver_hires.h5']
    sys.exit(main())
