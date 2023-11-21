# zero_kernel

An Android kernel with Kali NetHunter functionality.

## Contents

- [zero\_kernel](#zero_kernel)
  - [Contents](#contents)
  - [**Disclaimer**](#disclaimer)
  - [Kernel Features](#kernel-features)
  - [Supported ROMs](#supported-roms)
  - [Important Note](#important-note)
  - [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Kernel](#kernel)
    - [Assets](#assets)
    - [Bundle](#bundle)
  - [Examples](#examples)
  - [Credits](#credits)
  - [See also](#see-also)

## **Disclaimer**

**This kernel is made for educational purposes only.**

**I am not responsible for anything that may or may not happen to your device by installing any custom ROMs and/or kernels.**

**Anything you do with this kernel you do at your own risk. By using it, you take the responsibility upon yourself and in case of any issue you are not to blame me or other related contributors.**

## Kernel Features

The kernel has the following features:

- Kali NetHunter support;
- RTL8812/21AU + RTL8814AU + RTL8187 Wi-Fi drivers;
- packet injection support for internal Wi-Fi chipset;
- optional KernelSU support.

## Supported ROMs

For OnePlus 5/T devices:

- 4.4 Linux kernel version:
  - LineageOS;
  - ParanoidAndroid;
  - x_kernel supported (universal)*.
- 4.14 Linux kernel version:
  - ParanoidAndroid (unofficial & testing);
  - x-ft_kernel supported (universal)**.

\* -- this is mostly relevant to ROMs based on LineageOS; however, technically speaking, this includes ParanoidAndroid as well, which makes x_kernel-based builds universal.

\** -- this, **in theory**, is relevant to all 4.14-based ROMs for this device in existence.

## Important Note

The contents of each release include ROM builds compatible with corresponding kernel builds. These ROM files are **unmodified and mirrored from official sources**.

This can be verified with the checksums, which should be identical to the ones presented on the ROM project's official web page.

You can always download the same ROM file from official sources if you'd like. The mirroring in this repository is done due to the fact that some ROM projects remove their older builds once they become too outdated.

## Usage

The custom build wrapper consists of 3 main components:

- kernel builder;
- assets collector;
- kernel + assets bundler.

```help
$ python3 wrapper --help
usage: wrapper [-h] [--clean] {kernel,assets,bundle} ...

A custom wrapper for the zero_kernel.

positional arguments:
  {kernel,assets,bundle}
    kernel              build the kernel
    assets              collect assets
    bundle              build the kernel + collect assets

optional arguments:
  -h, --help            show this help message and exit
  --clean               clean the root directory
```

### Prerequisites

**It is highly recommended to use `docker` option to run this tool.** For that you need Docker Engine or Docker Desktop, depending on your OS.

To run this tool in a `local` environment, you will need:

- a Debian-based Linux distribution (other types of distros are untested);
- a few [packages](Dockerfile#L15) installed in your system.

You will also need a few Python packages. To install them, use:

```sh
python3 -m poetry install --no-root
```

To install `poetry`, use `python3 -m pip install poetry`.

### Kernel

Kernel build process can be launched by using the `python3 wrapper kernel <arguments>` command.

For more options you can refer to the help message below.

```help
$ python3 wrapper kernel --help
usage: wrapper kernel [-h] [-c] [--clean-image]
                      [--log-level {normal,verbose,quiet}] [-o OUTLOG] [--ksu]
                      {local,docker,podman} {los,pa,x} codename

positional arguments:
  {local,docker,podman}
                        select build environment
  {los,pa,x}            select a ROM for the build
  codename              select device codename

options:
  -h, --help            show this help message and exit
  -c, --clean           don't build anything, just clean the environment
  --clean-image         remove Docker/Podman image from the host machine after
                        build
  --log-level {normal,verbose,quiet}
                        select log level
  -o OUTLOG, --output OUTLOG
                        save logs to a file
  --ksu                 add KernelSU support
```

### Assets

As mentioned, there is also an asset downloader, which can collect latest versions of ROM, TWRP, Magisk and it's modules, Kali Chroot etc.

```help
$ python3 wrapper assets --help
usage: wrapper assets [-h] [--extra-assets EXTRA_ASSETS] [--rom-only]
                      [--clean-image] [--clean]
                      [--log-level {normal,verbose,quiet}] [-o OUTLOG] [--ksu]
                      {local,docker,podman} {los,pa,x} codename {full,minimal}

positional arguments:
  {local,docker,podman}
                        select build environment
  {los,pa,x}            select a ROM for the build
  codename              select device codename
  {full,minimal}        select Kali chroot type

options:
  -h, --help            show this help message and exit
  --extra-assets EXTRA_ASSETS
                        select a JSON file with extra assets
  --rom-only            download only the ROM as an asset
  --clean-image         remove Docker/Podman image from the host machine after
                        build
  --clean               autoclean 'assets' folder if it exists
  --log-level {normal,verbose,quiet}
                        select log level
  -o OUTLOG, --output OUTLOG
                        save logs to a file
  --ksu                 add KernelSU support
```

### Bundle

There is an option named `bundle` which combines build artifacts of both `kernel` and `assets` modules into a single package.

This is especially useful for linking the kernel version with the appropriate ROM version.

There are cases when an old kernel version is used with the newer ROM version (adapted for the *newer* version of kernel). Such cases can ultimately lead to your system working improperly or breaking down completely, which is why it is important to use a specific kernel build with a corresponding ROM build.

Currently, there are three types of packaging available:

- `conan`;
- `slim`;
- `full`.

Options `full` and `conan` collect all of the assets required to successfuly flash the kernel onto your device. The difference between the two is that `full` option places everything into a local directory, while `conan` organizes everything as a Conan package.

An option named `slim` is a much lighter version of `full` packaging, as only the ROM is collected from the asset list. This is done to reduce package sizes while ensuring the kernel+ROM compatibility.

```help
$ python3 wrapper bundle --help
usage: wrapper bundle [-h] [--conan-upload] [--clean-image]
                      [--log-level {normal,verbose,quiet}] [-o OUTLOG] [--ksu]
                      {local,docker,podman} {los,pa,x} codename
                      {conan,slim,full}

positional arguments:
  {local,docker,podman}
                        select build environment
  {los,pa,x}            select a ROM for the build
  codename              select device codename
  {conan,slim,full}     select package type of the bundle

options:
  -h, --help            show this help message and exit
  --conan-upload        upload Conan packages to remote
  --clean-image         remove Docker/Podman image from the host machine after
                        build
  --log-level {normal,verbose,quiet}
                        select log level
  -o OUTLOG, --output OUTLOG
                        save logs to a file
  --ksu                 add KernelSU support
```

## Examples

Here are some examples of commands:

- **(Recommended)** Build kernel and collect ROM via Docker:
  - `python3 wrapper bundle docker los dumpling slim`;
- Build kernel locally:
  - `python3 wrapper kernel local los dumpling`;
- Collect all the assets locally:
  - `python3 wrapper assets local los dumpling full`.

## Credits

- [x_kernel_oneplus_msm8998](https://github.com/ederekun/x_kernel_oneplus_msm8998): OnePlus 5/T kernel with many optimizations and improvements;
- [x-ft_kernel_oneplus_msm8998](https://github.com/ederekun/x-ft_kernel_oneplus_msm8998): 4.14-based variation of x_kernel;
- [kali-nethunter-kernel](https://gitlab.com/kalilinux/nethunter/build-scripts/kali-nethunter-kernel): official kernel patches from Kali NetHunter project.

## See also

- [FAQ](docs/FAQ.md);
- [TODO List](docs/TODO.md);
- [Kernel Flashing Instructions](docs/FLASHING.md).
