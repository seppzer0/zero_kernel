import os
import shutil
import requests
from pathlib import Path
from typing import List, Tuple

import wrapper.tools.messages as msg


def ucopy(src: os.PathLike, dst: os.PathLike, exceptions: List[str] = []) -> None:
    """A universal method to copy files into desired destinations.

    :param path src: Source path.
    :param path dst: Destination path.
    :param List[str] exceptions: Elements that will not be removed.
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


def replace_lines(filename: os.PathLike, og_lines: Tuple[str], nw_lines: Tuple[str]) -> None:
    """Replace lines in the specified file."""
    filename_new = Path(str(filename) + "_new")
    with open(filename) as data:
        with open(filename_new, 'w') as new_data:
            for line in data:
                for indx, key in enumerate(og_lines):
                    if key in line:
                        msg.note(f"Replacing {key} with {nw_lines[indx]}")
                        line = line.replace(key, nw_lines[indx])
                new_data.write(line)
    os.replace(filename_new, filename)
