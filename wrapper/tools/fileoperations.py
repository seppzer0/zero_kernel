import os
import shutil
import requests
from typing import Tuple
from pathlib import Path

import tools.messages as msg
import tools.commands as ccmd


def ucopy(src: Path, dst: Path, exceptions: Tuple[str] = ()) -> None:
    """A universal method to copy files into desired destinations.

    :param src: Source path.
    :param dst: Destination path.
    :param exceptions: Elements that will not be removed.
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

    :param url: URL to the file.
    """
    fn = url.split("/")[-1]
    msg.note(f"Downloading {fn} ..")
    print(f"      URL: {url}")
    try:
        if "sourceforge" in url:
            msg.note("Sorceforge URL detected, using wget..")
            fn = url.split("/download")[0].split("/")[-1]
            ccmd.launch(f"wget -O {fn} {url}")
        else:
            with requests.get(url, stream=True, headers={"referer": url}) as r:
                r.raise_for_status()
                with open(fn, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
    except Exception:
        msg.error("Download failed.")
    msg.done("Done!")


def replace_lines(filename: Path, og_lines: Tuple[str], nw_lines: Tuple[str]) -> None:
    """Replace lines in the specified file.

    :param filename: Path to the filename.
    :param og_lines: Original lines to be replaced.
    :param nw_lines: New lines in place of original lines.
    """
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


def replace_nth(filename: Path, og_string: str, nw_string: str, occurence: int) -> None:
    """Replace the n-th occurence of subtring in specified file.

    :param filename: Path to the filename.
    :param og_string: Original string to be replaced.
    :param nw_string: New string used to replace the original one.
    :param occurence: The index of occurence to replace.
    """
    filename_new = Path(str(filename) + "_new")
    with open(filename) as data:
        with open(filename_new, 'w') as new_data:
            counter = 0
            for line in data:
                if og_string in line:
                    counter += 1
                    if counter == occurence:
                        msg.note(f"Replacing {og_string} with {nw_string}")
                        line = line.replace(og_string, nw_string)
                new_data.write(line)
    os.replace(filename_new, filename)


def insert_before_line(filename: str, pointer_line: str, new_line: str) -> None:
    """Insert new line before the specified one.

    :param filename: Name of the file.
    :param pointer_line: The line before which new line will be inserted.
    :param new_line: The line being inserted.
    """
    with open(filename, "r+") as f:
        a = [x.rstrip() for x in f]
        index = 0
        for item in a:
            if item.startswith(pointer_line):
                a.insert(index, new_line)
                break
            index += 1
        f.seek(0)
        f.truncate()
        for line in a:
            f.write(line + "\n")


def apply_patch(filename: str) -> None:
    """Apply .patch file.

    :param filename: Name of the .patch file.
    """
    msg.note(f"Applying patch: {filename}")
    ccmd.launch(f"patch -p1 -s --no-backup-if-mismatch -i {filename}")
    os.remove(filename)
