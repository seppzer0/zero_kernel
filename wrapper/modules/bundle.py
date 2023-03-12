import os
import sys
import json
import shutil
import argparse
import itertools
import subprocess
# append to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import cleanmaster as cm
import customcmd as ccmd
import fileoperations as fo
import messagedecorator as msg


def parse_args():
    """Parse the script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("losversion",
                        help="select LineageOS version")
    parser.add_argument("codename",
                        help="select device codename")
    parser.add_argument("package_type",
                        help="select package type of the bundle")
    parser.add_argument("--rom-only",
                        dest="rom_only",
                        action="store_true",
                        help="download only the ROM as an asset")
    global args
    args = parser.parse_args()


def build_kernel(losver, clean_only=False):
    """Build the kernel."""
    cmd = f"python3 {os.path.join(workdir, 'wrapper', 'modules', 'kernel.py')} {args.codename} {losver}"
    if clean_only:
        cmd += " -c"
    if not os.path.isdir("kernel") or clean_only is True:
        ccmd.launch(cmd)


def collect_assets(losver, chroot):
    """Collect assets."""
    cmd = f"python3 {os.path.join(workdir, 'wrapper', 'modules', 'assets.py')} {args.codename} {losver} {chroot} --clean"
    if args.rom_only:
        cmd += " --rom-only"
    ccmd.launch(cmd)


def conan_sources():
    """Prepare sources for rebuildable Conan packages."""
    sourcedir = os.path.join(workdir, "source")
    print("\n", end="")
    msg.note("Copying sources for Conan packaging..")
    cm.remove(sourcedir, allow_errors=True)
    fo.ucopy(workdir, sourcedir, ["__pycache__",
                                  ".vscode",
                                  "source",
                                  "kernel",
                                  "localversion",
                                  "assets",
                                  "conanfile.py"])
    msg.done("Done!")


def conan_options(json_file):
    """Read Conan options from a JSON."""
    with open(json_file) as f:
        json_data = json.load(f)
    return json_data


def conan_package(options, reference):
    """Create the Conan package."""
    cmd = f"conan export-pkg . {reference}"
    for option_value in options:
        # not the best solution, but will work temporarily for 'losversion' and 'chroot' options
        option_name = "losversion" if not any(c.isalpha() for c in option_value) else "chroot"
        cmd += f" -o {option_name}={option_value}"
    # add codename as an option separately
    cmd += f" -o codename={args.codename}"
    ccmd.launch(cmd)


def conan_upload(reference):
    """Upload Conan component to the remote."""
    # configure Conan client and upload packages
    url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
    alias = "s0nhconan"
    cmd = f"conan remote add {alias} {url} && "\
          f"conan user -p {os.getenv('CONAN_PASSWORD')} -r {alias} {os.getenv('CONAN_LOGIN_USERNAME')} && "\
          f"conan upload -f {reference} -r {alias}"
    ccmd.launch(cmd)


# launch script
parse_args()
msg.outputstream()
workdir = os.getenv("ROOTPATH")
# get either a "kernel+ROM" or "kernel+assets=Conan" bundle (the latter is heavier)
if args.package_type == "generic-slim":
    build_kernel(args.losversion)
    collect_assets(args.losversion, "minimal")
    # make a unified "release-light" directory with both .zips
    reldir_light = "release-light"
    kdir = "kernel"
    adir = "assets"
    # copy kernel
    kfn = "".join(os.listdir(kdir))
    shutil.copy(os.path.join(workdir, kdir, kfn),
                os.path.join(workdir, reldir_light, kfn))
    # copy asset (ROM)
    afn = "".join(os.listdir(adir))
    shutil.copy(os.path.join(workdir, adir, afn),
                os.path.join(workdir, reldir_light, afn))
elif args.package_type == "conan":
    # form Conan reference
    name = os.getenv("KNAME")
    version = os.getenv("KVERSION")
    user = args.codename
    channel = "stable" if subprocess.check_output("git branch --show-current", shell=True).decode("utf-8").splitlines()[0] == "main" else "testing"
    reference = f"{name}/{version}@{user}/{channel}"
    # form option sets
    losversion = [args.losversion]
    chroot = ["minimal", "full"]
    option_sets = list(itertools.product(losversion, chroot))
    # build and upload Conan packages
    fo.ucopy(os.path.join(workdir, "conan"), workdir)
    for opset in option_sets:
        build_kernel(opset[0])
        build_kernel(opset[0], True)
        conan_sources()
        collect_assets(opset[0], opset[1])
        conan_package(opset, reference)
    # upload packages
    if os.getenv("CONAN_UPLOAD_CUSTOM") == "1":
        conan_upload(reference)
os.chdir(workdir)
