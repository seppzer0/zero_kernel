import io
import os
import sys
import json
import argparse
import platform
import tools.customcmd as ccmd
import tools.cleanmaster as cm
import tools.fileoperations as fo
import tools.messagedecorator as msg


def parse_args() -> argparse.Namespace:
    """Parse the script arguments."""
    # show the 'help' message if no arguments supplied
    args = None if sys.argv[1:] else ["-h"]
    # parser and subparsers
    parser_parent = argparse.ArgumentParser(description="A custom wrapper for the s0nh kernel.")
    subparsers = parser_parent.add_subparsers(dest="command")
    parser_kernel = subparsers.add_parser("kernel", help="build the kernel")
    parser_assets = subparsers.add_parser("assets", help="collect assets")
    parser_bundle = subparsers.add_parser("bundle", help="build the kernel + collect assets")
    # add a single argument for the main parser
    parser_parent.add_argument("--clean",
                               action="store_true",
                               help="clean the root directory")
    # common argument attributes for subparsers
    help_losversion = "select LineageOS version"
    help_codename = "select device codename"
    help_buildenv = "select build environment"
    help_clean = "remove Docker/Podman image from the host machine after build"
    help_loglvl = "select log level"
    choices_buildenv = ["local", "docker", "podman"]
    choices_loglvl = ["normal", "verbose", "quiet"]
    default_loglvl = "normal"
    help_logfile = "save logs to a file"
    # kernel
    parser_kernel.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_kernel.add_argument("losversion",
                               help=help_losversion)
    parser_kernel.add_argument("codename",
                               help=help_codename)
    parser_kernel.add_argument("-c", "--clean",
                               dest="clean",
                               action="store_true",
                               help="don't build anything, just clean the environment")
    parser_kernel.add_argument("--clean-docker",
                               action="store_true",
                               dest="clean_image",
                               help=help_clean)
    parser_kernel.add_argument("--log-level",
                               dest="loglvl",
                               choices=choices_loglvl,
                               default=default_loglvl,
                               help=help_loglvl)
    parser_kernel.add_argument("-o", "--output",
                               dest="outlog",
                               help=help_logfile)
    # assets
    parser_assets.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_assets.add_argument("losversion",
                               help=help_losversion)
    parser_assets.add_argument("codename",
                               help=help_codename)
    parser_assets.add_argument("chroot",
                               choices=["full", "minimal"],
                               help="select Kali chroot type")
    parser_assets.add_argument("--extra-assets",
                               dest="extra_assets",
                               help="select a JSON file with extra assets")
    parser_assets.add_argument("--clean-image",
                               action="store_true",
                               dest="clean_image",
                               help=help_clean)
    parser_assets.add_argument("--clean",
                               dest="clean",
                               action="store_true",
                               help="autoclean 'assets' folder if it exists")
    parser_assets.add_argument("--log-level",
                               dest="loglvl",
                               choices=choices_loglvl,
                               default=default_loglvl,
                               help=help_loglvl)
    parser_assets.add_argument("-o", "--output",
                               dest="outlog",
                               help=help_logfile)
    # bundle
    parser_bundle.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_bundle.add_argument("losversion",
                               help=help_losversion)
    parser_bundle.add_argument("codename",
                               help=help_codename)
    parser_bundle.add_argument("--conan-cache",
                               action="store_true",
                               dest="conan_cache",
                               help="mount Conan cache into Docker container")
    parser_bundle.add_argument("--conan-upload",
                               action="store_true",
                               dest="conan_upload",
                               help="upload Conan packages to remote")
    parser_bundle.add_argument("--clean-docker",
                               action="store_true",
                               dest="clean_image",
                               help=help_clean)
    parser_bundle.add_argument("--log-level",
                               dest="loglvl",
                               choices=choices_loglvl,
                               default=default_loglvl,
                               help=help_loglvl)
    parser_bundle.add_argument("-o", "--output",
                               dest="outlog",
                               help=help_logfile)
    return parser_parent.parse_args(args)


def validate_settings(codename, buildenv):
    """Run settings validations."""
    # detect OS family
    if buildenv == "local":
        if not platform.system() == "Linux":
            msg.error("Can't build Linux kernel on a non-Unix machine.")
        else:
            # check that it is Debian-based
            try:
                ccmd.launch("apt --version", "quiet")
            except Exception as e:
                msg.error("Detected Linux distribution is not Debian-based, unable to launch.")
    # check if specified device is supported
    with open(os.path.join(os.getenv("ROOTPATH"), "manifests", "devices.json")) as f:
        devices = json.load(f)
    if codename not in devices.keys():
        msg.error("Unsupported device codename specified.")


def form_cmd(args: argparse.Namespace, name_script, name_docker="", wdir=""):
    """Form a command to run the build."""
    # override path for execution within Docker
    if args.buildenv == "docker":
        os.environ["ROOTPATH"] = os.path.join("/", wdir)
    # declare base cmd
    base_cmd = f"python3 {os.path.join(os.getenv('ROOTPATH'), 'wrapper', 'modules', name_script)}"
    cmd = base_cmd
    # wrap the command into Docker
    if args.buildenv == "docker":
        cmd = f'{args.buildenv} run -it --rm -e ROOTPATH={os.getenv("ROOTPATH")} -w /{wdir} {name_docker} /bin/bash -c "{cmd}"'
        # mount directories
        if args.command == "kernel":
            reldir = "release"
            if not os.path.isdir(reldir):
                os.mkdir(reldir)
            cmd = cmd.replace(f'-w /{wdir}',
                              f'-w /{wdir} '\
                              f'-v $(pwd)/{reldir}:/{wdir}/{reldir}')
        elif args.command == "assets":
            assetsdir = "assets"
            if not os.path.isdir(assetsdir):
                os.mkdir(assetsdir)
            cmd = cmd.replace(f'-w /{wdir}',
                              f'-w /{wdir} '\
                              f'-v $(pwd)/{assetsdir}:/{wdir}/{assetsdir}')
        # setup Conan client
        if args.command == "bundle":
            if args.conan_upload:
                cmd = cmd.replace(f'-w /{wdir}',
                                  f'-e CONAN_UPLOAD_CUSTOM=1 -w /{wdir}')
            if args.conan_cache:
                # set proper permissions on mounted .conan directory
                cmd = cmd.replace(base_cmd, base_cmd + " && chmod 777 -R /root/.conan")
                # determine the path to local Conan cache and check if it exists
                conan_cache_dir = ""
                if os.getenv("CONAN_USER_HOME"):
                    conan_cache_dir = os.getenv("CONAN_USER_HOME")
                else:
                    conan_cache_dir = os.path.join(os.getenv("HOME"), ".conan")
                if os.path.isdir(conan_cache_dir):
                    cmd = cmd.replace(f'-w /{wdir}',
                                      f'-w /{wdir} -v {conan_cache_dir}:/"/root/.conan"')
                else:
                    msg.error("Could not find Conan local cache on the host machine.")
    return cmd


def main(args: argparse.Namespace):
    # various environment preparations
    os.environ["ROOTPATH"] = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(os.getenv("ROOTPATH"))
    if args.clean:
        cm.root()
        sys.exit(0)
    os.environ["LOGLEVEL"] = args.loglvl
    with open(os.path.join(os.getenv("ROOTPATH"), "manifests", "info.json")) as f:
        data = json.load(f)
        os.environ["KNAME"] = data["name"]
        os.environ["KVERSION"] = data["version"]
    validate_settings(args.codename, args.buildenv)
    docker_name = "s0nhbuilder"
    docker_wdir = "s0nhbuild"
    script = ""
    # setup output stream
    if args.command and args.outlog:
        msg.note(f"Writing output to {args.outlog}")
        if args.outlog in os.listdir():
            os.remove(args.outlog)
        os.environ["OSTREAM"] = args.outlog
        msg.outputstream()
    # determine script and it's arguments
    if args.command == "kernel":
        script = f"kernel.py {args.codename} {args.losversion}"
        if args.clean:
            script += " -c"
    elif args.command == "assets":
        script = f"assets.py {args.codename} {args.losversion} {args.chroot}"
        if args.extra_assets:
            script += " --extra-assets"
    elif args.command == "bundle":
        script = f"bundle.py {args.losversion} {args.codename}"
        if args.conan_upload:
            script += " --conan-upload"
    workdir = os.path.dirname(os.path.realpath(sys.argv[0]))
    conan_cache = os.path.join(os.getenv("HOME"), ".conan")
    # build isolated image (using Docker BuildKit or Podman)
    if args.buildenv in ["docker", "podman"]:
        os.environ["DOCKER_BUILDKIT"] = "1"
        ccmd.launch(f"{args.buildenv} build . -f docker{os.sep}Dockerfile -t {docker_name}")
    # launch the selected wrapper component
    ccmd.launch(form_cmd(args, script, docker_name, docker_wdir))
    # clean Docker/Podman image from host machine after the build
    if args.clean_image:
        ccmd.launch(f"{args.buildenv} rmi {docker_name}")


if __name__ == '__main__':
    main(parse_args())
