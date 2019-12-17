#!/usr/local/bin/python3

from argparse import ArgumentParser
import exifread  # read exif metadata
import os, sys

def rename_photos():
    '''
    Rename photo(s) based on the creation time using the format:
        yyyymmdd_hhmmss(_cc)
    where cc represents a potential duplicate counter (to make sure files don't get overwritten).
    Acceptable file formats: nef, dng, jpg, jpeg
    '''

    # set up command-line options
    info = 'Rename photo(s) based on the creation time using the format yyyymmdd_hhmmss(_cc) \
            where cc represents a potential duplicate counter. \
            Acceptable file formats: nef, dng, jpg, jpeg'
    parser = ArgumentParser(description=info, add_help=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', metavar='name', help='process named file')
    group.add_argument('-p', '--path', metavar='name', help='process files in named location')
    args = parser.parse_args()

    # parse arguments
    path = None
    files = None
    if args.file is not None and os.path.isfile(args.file):
        data = args.file.rpartition('/')
        path = data[0] + data[1]
        files = [data[2]]
    elif args.path is not None and os.path.isdir(args.path):
        path = args.path if args.path[-1] == '/' else args.path + '/'  # path must end with '/'
        files = os.listdir(path)
    else:
        print('\nplease provide a valid file or path name\n')
        return

    # store generated names to check for duplicates
    names = dict()

    # valid file extensions
    ftypes = ['nef', 'dng', 'jpg', 'jpeg']

    # process files
    for file in files:
        ftype = file.split('.')[-1].lower()

        # skip if directory, hidden file, or invalid file type
        if not os.path.isfile(path + file) or file.startswith('.') or ftype not in ftypes:
            print ('\n"' + file + '" is not a valid file...skipping\n')
            continue

        # read exif data
        photo = open(path + file, 'rb')
        data = exifread.process_file(photo)
        photo.close()

        # skip if file creation time not found
        if 'EXIF DateTimeOriginal' not in data.keys():
            print ('\nunable to extract creation time from "' + file + '"...skipping\n')
            continue

        # construct new name as: yyyymmdd_hhmmss(_cc)
        name = str(data['EXIF DateTimeOriginal']).replace(' ', '_').replace(':', '')
        if name not in names:
            names[name] = 1
        else:
            names[name] += 1
            name += '_{:0>2}'.format(names[name])
        name += '.' + ftype

        # rename file
        print ('renaming ' + file + '\tto\t' + name)
        os.rename(path + file, path + name)

if __name__ == '__main__':
    rename_photos()
