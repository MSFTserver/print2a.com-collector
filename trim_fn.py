import os, sys, shutil

cwd = "C:\\Users\\HostsServer\\Downloads\\p2aup"

dirs = [ name for name in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, name)) ]

# detect if the subdirectory has same name as parent directory if it does move it to the parent directory
for dir in dirs:
    #print(dir)
    folder = os.path.join(cwd, dir)
    folders = [ name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder, name)) ]
    for subfolder in folders:
        if subfolder == os.path.basename(folder):
            shutil.move(os.path.join(folder, subfolder), folder+'_p2aup1')
            shutil.rmtree(folder,ignore_errors=True)
            os.rename(folder+'_p2aup1', folder)