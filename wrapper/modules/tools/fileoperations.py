import os
import shutil
import requests
from . import messagedecorator as msg


def ucopy(src, dst, exceptions=[]):
    """A universal method to copy files into desired destinations."""
    # for a directory (it's contents)
    if os.path.isdir(src):
        if not os.path.isdir(dst):
            os.mkdir(dst)
        contents = os.listdir(src)
        for e in contents:
            # do not copy restricted files
            if e not in exceptions and e != src:
                src_e = os.path.join(src, e)
                dst_e = os.path.join(dst, e)
                if os.path.isdir(src_e):
                    shutil.copytree(src_e, dst_e)
                elif os.path.isfile(src_e):
                    shutil.copy(src_e, dst_e)
    # for a single file
    elif os.path.isfile(src):
        shutil.copy(src, dst)


#def download(url):
#    """A simple downloader."""
#    file = url.split("/")[-1]
#    msg.note(f"Downloading {file} ..")
#    print(f"      URL: {url}")
#    try:
#        open(file, "wb").write(requests.get(url).content)
#    except Exception:
#        msg.error("Download failed.")
#    msg.done("Done!")

def download(url):
    """A simple file downloader."""
    file = url.split("/")[-1]
    msg.note(f"Downloading {file} ..")
    print(f"      URL: {url}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
    except Exception:
        msg.error("Download failed.")
    msg.done("Done!")
