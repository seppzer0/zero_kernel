import os
import shutil
import requests
from typing import List
from pathlib import Path

import wrapper.tools.messages as msg


def ucopy(src: os.PathLike, dst: os.PathLike, exceptions: List[str] = []) -> None:
    """A universal method to copy files into desired destinations.

    :param path src: Source path.
    :param path dst: Destination path.
    :param path exceptions: Elements that will not be removed.
    """
    # for a directory (it's contents)
    if src.is_dir():
        if not dst.is_dir():
            os.mkdir(dst)
        contents = os.listdir(src)
        for e in contents:
            # do not copy restricted files
            if e not in exceptions and e != src:
                src_e = Path(src, e)
                dst_e = Path(dst, e)
                if src_e.is_dir():
                    shutil.copytree(src_e, dst_e)
                elif src_e.is_file():
                    shutil.copy(src_e, dst_e)
    # for a single file
    elif src.is_file():
        shutil.copy(src, dst)


def download(url: str) -> None:
    """A simple file downloader.

    :param str url: URL to the file.
    """
    fn = url.split("/")[-1]
    msg.note(f"Downloading {fn} ..")
    print(f"      URL: {url}")
    try:
        # URL for TWRP is weird, have to adjust the query
        if "twrp" in url:
            with requests.get(url, stream=True, headers={"referer": url}) as r:
                r.raise_for_status()
                with open(fn, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
        else:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(fn, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
    except Exception:
        msg.error("Download failed.")
    msg.done("Done!")
