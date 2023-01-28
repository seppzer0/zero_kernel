import io
import os
import sys
import shutil
import argparse
import tools.customcmd as ccmd
import tools.fileoperations as fo


def parse_args() -> argparse.Namespace:
    """Parse the script arguments."""
    # show the 'help' message if no arguments supplied
    args = None if sys.argv[1:] else ["-h"]
    # parser and subparsers
    main_parser = argparse.ArgumentParser(description="A custom wrapper for the s0nh kernel.")
    subparsers = main_parser.add_subparsers(dest="command")
    parser_kernel = subparsers.add_parser("kernel", help="build the kernel")
    parser_assets = subparsers.add_parser("assets", help="collect assets")
    parser_bundle = subparsers.add_parser("bundle", help="build the kernel + collect assets")
    # common argument attributes
    help_losversion = "select LineageOS version"
    help_codename = "select device codename"
    help_buildenv = "select whether this is a 'local' or 'docker' build"
    help_clean = "remove Docker image from the host machine after build"
    help_loglvl = "select log level"
    choices_buildenv = ["local", "docker"]
    choices_codename = ["dumpling", "cheeseburger"]
    choices_loglvl = ["normal", "verbose", "quiet"]
    default_loglvl = "normal"
    # kernel
    parser_kernel.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_kernel.add_argument("losversion",
                               help=help_losversion)
    parser_kernel.add_argument("codename",
                               choices=choices_codename,
                               help=help_codename)
    parser_kernel.add_argument("-c", "--clean",
                               dest="clean",
                               action="store_true",
                               help="don't build anything, just clean the environment")
    parser_kernel.add_argument("--clean-docker",
                               action="store_true",
                               dest="clean_docker",
                               help=help_clean)
    parser_kernel.add_argument("--log-level",
                               dest="loglvl",
                               choices=choices_loglvl,
                               default=default_loglvl,
                               help=help_loglvl)
    # assets
    parser_assets.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_assets.add_argument("losversion",
                               help=help_losversion)
    parser_assets.add_argument("codename",
                               choices=choices_codename,
                               help=help_codename)
    parser_assets.add_argument("chroot",
                               choices=["full", "minimal"],
                               help="select Kali chroot type")
    parser_assets.add_argument("--extra-assets",
                               dest="extra_assets",
                               help="select a JSON file with extra assets")
    parser_assets.add_argument("--clean-docker",
                               action="store_true",
                               dest="clean_docker",
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
    # bundle
    parser_bundle.add_argument("buildenv",
                               choices=choices_buildenv,
                               help=help_buildenv)
    parser_bundle.add_argument("losversion",
                               help=help_losversion)
    parser_bundle.add_argument("codename",
                               choices=choices_codename,
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
                               dest="clean_docker",
                               help=help_clean)
    parser_bundle.add_argument("--log-level",
                               dest="loglvl",
                               choices=choices_loglvl,
                               default=default_loglvl,
                               help=help_loglvl)
    return main_parser.parse_args(args)


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
        cmd = f'docker run -it --rm -e ROOTPATH={os.getenv("ROOTPATH")} -w /{wdir} {name_docker} /bin/bash -c "{cmd}"'
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
        # set up Conan client
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
    # this is for logs to get shown properly in various build systems
    sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), 'wb', 0), write_through=True)
    # share environment variables across all modules
    os.environ["LOGLEVEL"] = args.loglvl
    os.environ["ROOTPATH"] = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(os.getenv("ROOTPATH"))
    # build the image and deploy the container
    docker_name = "s0nhbuilder"
    docker_wdir = "s0nhbuild"
    script = ""
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
    # build Docker image and create a container
    if args.buildenv == "docker":
        fo.ucopy(os.path.join(workdir, "docker"),
                 os.path.join(workdir))
        os.chdir(os.path.join(workdir))
        ccmd.launch(f"docker build . -t {docker_name}")
        # remove Docker files after the build
        docker_files = ["Dockerfile", ".dockerignore"]
        for f in docker_files:
            os.remove(os.path.join(workdir, f))
    # launch the selected wrapper module
    ccmd.launch(form_cmd(args, script, docker_name, docker_wdir))
    # clean Docker image from host machine after the build
    if args.clean_docker:
        ccmd.launch(f"docker rmi {docker_name}")


if __name__ == '__main__':
    main(parse_args())
