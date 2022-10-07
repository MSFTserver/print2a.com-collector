#!/usr/bin/env python3
'''
Use lbrytools to download data from the specified channel.

NOTE: You need to install lbrytools from here:
    https://github.com/belikor/lbrytools

You can create a virtual env and then just copy the whole git dir
inside lib/python3.X/site-packages

This abuses the default sort order of the results from
lbrytools.ch_download_latest(), which sorts on the timestamps.
So just find the number of entries with a timestamp later than the ts
you want using lbrytools.ch_search_n_claims(), then call
lbrytools.ch_download_latest() for that many entries.
'''
from datetime import datetime
from typing import Optional
import lbrytools as lt
import os, sys, argparse, shutil, patoolib, re, time

cwd = os.getcwd()
dl_path = "D:\\print2a-master-folder\\p2aup-test"
unfriendly = ["?","!","[","]",";",":","*","/","\\","}","{","(",")","'",'"']
reg_unfriendly = ["?","!","[","\]",";",":","*","/","\\","}","{","(",")","'",'"']
video_ext_list = ['.3g2', '.3gp', '.amv', '.asf', '.avi', '.f4a', '.f4b', '.f4p',
                  '.f4v', '.flv', '.flv', '.gifv', '.m4p', '.m4v', '.m4v', '.mkv',
                  '.mng', '.mod', '.mov', '.mp2', '.mp4', '.mpe', '.mpeg', '.mpg',
                  '.mpv', '.mxf', '.nsv', '.ogg', '.ogv', '.qt', '.rm', '.roq', 
                  '.rrc', '.svi', '.vob', '.webm', '.wmv', '.yuv']
archive_ext_list = ['.7z', '.a', '.ace', '.adf', '.alz', '.ape', '.arc', '.arj',
                    '.bz2', '.cab', '.cb7', '.cba', '.cbr', '.cbt', '.cbz', '.cpio',
                    '.dms', '.flac', '.gz', '.jar', '.lha', '.lrz', '.lz', '.lzh', 
                    '.lzma', '.lzo', '.rar', '.rpm', '.rz', '.shn', '.tar', '.xz', 
                    '.Z', '.zip', '.zoo']
audio_ext_list = ['.aac', '.aiff', '.ape', '.au', '.flac', '.gsm', '.it', '.m3u', 
                  '.m4a', '.mid', '.mod', '.mp3', '.mpa', '.pls', '.ra', '.s3m', 
                  '.sid', '.wav', '.wma', '.xm']
image_ext_list = ['.3dv', '.ai', '.amf', '.art', '.art', '.ase', '.awg', '.blp', 
                  '.bmp', '.bw', '.bw', '.cd5', '.cdr', '.cgm', '.cit', '.cmx', 
                  '.cpt', '.cr2', '.cur', '.cut', '.dds', '.dib', '.djvu', '.dxf', 
                  '.e2d', '.ecw', '.egt', '.egt', '.emf', '.eps', '.exif', '.fs', 
                  '.gbr', '.gif', '.gpl', '.grf', '.hdp', '.heic', '.heif' '.icns', 
                  '.ico', '.iff', '.iff', '.int', '.int', '.inta', '.jfif', '.jng', 
                  '.jp2', '.jpeg', '.jpg', '.jps', '.jxr', '.lbm', '.lbm', '.liff', 
                  '.max', '.miff', '.mng', '.msp', '.nef', '.nitf', '.nrrd', '.odg', 
                  '.ota', '.pam', '.pbm', '.pc1', '.pc2', '.pc3', '.pcf', '.pct', 
                  '.pcx', '.pcx', '.pdd', '.pdn', '.pgf', '.pgm', '.PI1', '.PI2', 
                  '.PI3', '.pict', '.png', '.pnm', '.pns', '.ppm', '.psb', '.psd', 
                  '.psp', '.px', '.pxm', '.pxr', '.qfx', '.ras', '.raw', '.rgb', 
                  '.rgb', '.rgba', '.rle', '.sct', '.sgi', '.sgi', '.sid', 
                  '.sun', '.svg', '.sxd', '.tga', '.tga', '.tif', '.tiff', '.v2d', 
                  '.vnd', '.vrml', '.vtf', '.wdp', '.webp', '.wmf', '.x3d', '.xar', 
                  '.xbm', '.xcf', '.xpm', ]
channels_list = [s.replace("https://odysee.com/", "").replace(":","#") for s in open("links.txt").readlines()]

# Globals:
MAX_SEARCH_CLAIMS = 10000
SERVER = 'http://localhost:5279'
TS_FORMAT = '%Y-%m-%d'

def find_num_downloads(channel: str, dt: datetime) -> int:
    '''
    Search a channel for the number of claims since a specified datetime.
    '''
    def _filter_claims_by_date(x):
        '''
        Filter the claims by their date.
        Compare with dt.
        '''
        return datetime.fromtimestamp(
                int(x['meta']['creation_timestamp']), # Unix ts
            ) > dt
    try:
        all_claims = lt.ch_search_n_claims(channel,
                                           number=MAX_SEARCH_CLAIMS,
                                           server=SERVER).get('claims')
        return len(list(filter(_filter_claims_by_date, all_claims)))
    except (TypeError, KeyError, ValueError):
        # Our search fucked up. We can potentially try
        # to handle it here, but for now just immediately raise it.
        raise

def traverse_dir(dir):
    '''
    Recusively Traverse a directory and remove all folders that only inlcude 1 directory and flatten
     From This   -->   Into this
        top      -->      top
         |       -->     /   \
        foo      -->    bar  baz
       /   \     -->   /  \     \
      bar  baz   --> car  caz    baz
     /  \     \  -->
   car  caz   car--> 
    '''
    for dir,subdir,listfilename in os.walk(dir):
        if len(subdir) == 1 and not len(listfilename):
            for dir,subdir,listfilename in os.walk(os.path.join(dir,subdir[0])):
                for new_dir in subdir:
                    shutil.move(os.path.join(dir,new_dir),dir.rsplit(os.path.sep, 1)[0])
                for filename in listfilename:
                    shutil.move(os.path.join(dir,filename),dir.rsplit(os.path.sep, 1)[0])
                shutil.rmtree(os.path.join(dir))
                dir = dir.rsplit(os.path.sep, 1)[0]
            for new_dir in subdir:
                subdir = [ name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name)) ]
                traverse_dir(dir)

def remove_dup_folders(rm_folder,project_name):
    '''
    Remove duplicate folders due to extra folders created by extracting files
     From This   -->   Into this
        top      -->      top
         |       -->     /   \
        foo      -->    bar  baz
       /   \     -->
      bar  baz   -->
    '''
    dirs = [ name for name in os.listdir(rm_folder) if os.path.isdir(os.path.join(rm_folder, name)) ]
    files = [ name for name in os.listdir(rm_folder) if not os.path.isdir(os.path.join(rm_folder, name)) ]
    if len(dirs) == 1 and len(files) == 0:
        for dir,subdir,listfilename in os.walk(os.path.join(rm_folder, dirs[0])):
            for filename in listfilename:
                shutil.move(os.path.join(dir, filename), dir.rsplit(os.path.sep, 1)[0])
            for dir in subdir:
                for dir,subdir,listfilename in os.walk(os.path.join(rm_folder, dirs[0], dir)):
                    shutil.move(dir, rm_folder)
        shutil.rmtree(os.path.join(rm_folder, dirs[0]))
        dirs = [ name for name in os.listdir(rm_folder) if os.path.isdir(os.path.join(rm_folder, name)) ]
    for dir in dirs:
        traverse_dir(os.path.join(rm_folder, dir))
        


def extract_archives(root_path, channel_name):
    '''
    Extract all archives in the given path
    also sorts out images, videos and audio files into seperate directories
    if a file doesnt match any of these it is put in its own folder with same name as the file
    '''
    for dir,subdir,listfilename in os.walk(root_path):
            for file in os.listdir(dir):
                name, ext = os.path.splitext(file)
                out_path = os.path.join(root_path, name)
                print(dir)
                if ext in archive_ext_list:
                    os.makedirs(out_path, exist_ok=True)
                    print(f'Extracting {name}')
                    patoolib.extract_archive(os.path.join(root_path, dir, file), outdir=out_path, verbosity=-1)
                    remove_dup_folders(out_path,channel_name)
                    os.remove(os.path.join(root_path, dir, file))
                elif ext in video_ext_list:
                    video_path = os.path.join(root_path, f'{channel_name}-videos')
                    os.makedirs(video_path, exist_ok=True)
                    shutil.move(os.path.join(root_path, dir, file), video_path)
                elif ext in audio_ext_list:
                    audio_path = os.path.join(root_path, f'{channel_name}-audio')
                    os.makedirs(audio_path, exist_ok=True)
                    shutil.move(os.path.join(root_path, dir, file), audio_path)
                elif ext in image_ext_list:
                    images_path = os.path.join(root_path, f'{channel_name}-images')
                    os.makedirs(images_path, exist_ok=True)
                    shutil.move(os.path.join(root_path, dir, file), images_path)
                elif os.path.isdir(os.path.join(root_path, dir, file)):
                    continue
                else:
                    misc_path = os.path.join(root_path, f'{channel_name}-misc')
                    os.makedirs(misc_path, exist_ok=True)
                    shutil.move(os.path.join(root_path, dir, file), misc_path)
    print("done extracting files!")
    

def _download(channel: str,
              max_downloads: int,
              download_path: Optional[str] = None) -> None:
    '''
    Download a channel, grabbing all claims newer than download_date,
    that aren't in the dowload_path already.
    '''
    downloaded_file = lt.ch_download_latest(
        channel=channel,
        number=max_downloads,
        ddir=download_path,
        save_file=True,
        repost=False,
        server=SERVER
    )
    dl_metadata = [sub['metadata'] for sub in downloaded_file]
    dl_title = [sub['claim_name'] for sub in downloaded_file][0]
    dl_desc = [sub['description'] for sub in dl_metadata][0]
    dl_source = [sub['source'] for sub in dl_metadata]
    dl_size = int([sub['size'] for sub in dl_source][0])
    dl_filename = [sub['file_name'] for sub in downloaded_file][0]
    dl_path = [sub['download_path'] for sub in downloaded_file][0]
    dl_dir = [sub['download_directory'] for sub in downloaded_file][0]
    channel_name = dl_dir.rsplit('\\',1)[1]
    url_channel_name, url_channel_claim = channel_name.rsplit('_',1)
    new_filename, ext = dl_filename.rsplit('.',1)
    print(os.path.exists(dl_path))
    file_size = os.stat(dl_path).st_size
    print("downloading...")
    while not dl_size == file_size:
        file_size = os.stat(dl_path).st_size
        print(f'{file_size}/{dl_size}')
        time.sleep(1)
    print(f"Extracting Archive...")
    extract_archives(dl_dir,channel_name)
    if "."+ext in archive_ext_list:
        desc_path = os.path.join(dl_dir, new_filename, f'lbry_description.md')
        f = open(desc_path, "w+")
        f.write(
            dl_desc+
            f'this file was auto created by print2a.com custom lbry collector, it is the description taken from the downloaded upload on the lbry/odysee post @ https://odysee.com/{url_channel_name}:{url_channel_claim}/{dl_title} \n\n'
        )
        f.close()
    else :
        desc_path = os.path.join(dl_dir, f'lbry_description.md')
        f = open(desc_path, "w+")
        f.write(dl_desc)
        f.close()

def download_channel(channel: str,
                     download_date: datetime,
                     download_path: Optional[str] = None) -> None:
    '''
    Download a channel. First fetch info on the number of downloads we should
    be doing using find_num_downloads(), then run the download process
    with _download().
    '''
    num_downloads = find_num_downloads(channel, download_date)
    _download(channel, num_downloads, download_path)

def rename(dir, is_dir, filename, new_filename, join_filenames):
    '''
    Rename a file.
    '''
    if is_dir:
        os.rename(dir, f'{os.path.dirname(dir)}{os.path.sep}{new_filename}')
    else:
        os.rename(os.path.join(dir, filename), os.path.join(dir, new_filename))

def sanitize_names(dir, name, is_dir):
    '''
    Sanitize a name removing certain characters that dont work on windows or unix or are not URL friendly
    '''
    if " " in name:
        join_filenames = "_"
        fn_parts = [w for w in name.split(" ")]
        new_filename = join_filenames.join(fn_parts)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    if "%" in name:
        join_filenames = "percent"
        fn_parts = [w for w in name.split('%')]
        new_filename = join_filenames.join(fn_parts)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    if "&" in name:
        join_filenames = "and"
        fn_parts = [w for w in name.split('&')]
        new_filename = join_filenames.join(fn_parts)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    if "+" in name:
        join_filenames = "plus"
        fn_parts = [w for w in name.split('_-_')]
        new_filename = join_filenames.join(fn_parts)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    if any(char in name for char in unfriendly):
        join_filenames = ""
        joined_unfriendly = join_filenames.join(reg_unfriendly)
        new_filename = re.sub(f'[{joined_unfriendly}]', join_filenames, name)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    if any(char in name for char in ["_-_", "_-", "-_"]):
        join_filenames = "-"
        joined_unfriendly = "|".join(["_-_", "_-", "-_"])
        new_filename = re.sub(f'{joined_unfriendly}', join_filenames, name)
        rename(dir, is_dir, name, new_filename, join_filenames)
        name = new_filename
        if is_dir:
            dir = f'{os.path.dirname(dir)}{os.path.sep}{name}'
    return dir

def make_friendly(path,self_called=False):
    '''
    check wether the given path is a directory or a file
    if it is a directory, it will be renamed to a friendly name and new dir path will be ruturned from the santizer
    if it is a file, it will be renamed to a friendly name
    if the directory includes subdirs we recursively call this function on them.
    '''
    for dir,subdir,listfilename in os.walk(path):
        if not self_called:
            print(dir.replace(dl_path,""))
        if dir != path:
            dir = sanitize_names(dir, os.path.basename(dir), True)
        for filename in listfilename:
            sanitize_names(dir, filename, False)
        if subdir:
            for new_dir in subdir:
                make_friendly(os.path.join(dir,new_dir),True)

def main() -> None:
    '''
    Argument parser and main function.
    '''
    parser = argparse.ArgumentParser(description='Run a fetch of a LBRY channel')
    parser.add_argument('-p', '--path', dest='path',
                        type=str, required=False)
    parser.add_argument('-d', '--after-date', dest='after_date',
                        type=str, required=False)
    args = parser.parse_args()
    if not args.path:
        download_path = dl_path
    else:
        download_path = args.path
    if not args.after_date:
        dt = datetime.fromtimestamp(0)  # First unix timestamp
    else:
        try:
            dt = datetime.strptime(args.after_date, TS_FORMAT)
        except (TypeError, ValueError) as err:
            print(f'INVALID date: {args.after_date}')
            print(f'Use timestamp format: {TS_FORMAT}')
            print(f'Exception caught: {repr(err)}')
            sys.exit(1)
    print(f'Downloading from {dt} to current time')
    print(f'Downloading to {download_path}')
    print(f'Downloading from a total of {len(channels_list)} channels')
    for channel_name in channels_list:
        try:
            print(f'Downloading from {channel_name}...')
            download_channel(channel_name, dt, download_path)
        except (TypeError, ValueError, KeyError) as err:
            print(f'Caught exception while downloading channel {channel_name}')
            print(f'Exception caught: {repr(err)}')
            sys.exit(1)
    print(f"Sanitizing folder and file names...")
    print("Checked Directories : (list will populate as directories are traversed)")
    make_friendly(dl_path)
    sys.exit(0)

if __name__ == '__main__':
    main()
