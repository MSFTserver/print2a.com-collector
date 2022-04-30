import os, shutil, patoolib

cwd = "C:\\Users\\HostsServer\\Downloads\\p2aup - Copy"

def remove_dup_folders(rm_folder):
    dirs = [ name for name in os.listdir(rm_folder) if os.path.isdir(os.path.join(rm_folder, name)) ]

    # detect if the subdirectory has same name as parent directory if it does move it to the parent directory
    for dir in dirs:
        #print(dir)
        folder = os.path.join(rm_folder, dir)
        folders = [ name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder, name)) ]
        for subfolder in folders:
            if subfolder == os.path.basename(folder):
                shutil.move(os.path.join(folder, subfolder), folder+'_p2aup1')
                shutil.rmtree(folder,ignore_errors=True)
                os.rename(folder+'_p2aup1', folder)

def extract_rar(root_path):
    for file in os.listdir(root_path):
        name, ext = os.path.splitext(file)
        out_path = f'{root_path}{os.path.sep}{name}'
        if ext == 'rar':
            print(file)
            patoolib.extract_archive(os.path.join(root_path, file), outdir=out_path)
            remove_dup_folders(out_path)
            os.remove(os.path.join(root_path, file))

