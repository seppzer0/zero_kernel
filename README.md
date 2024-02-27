# zero_kernel

An advanced Android kernel builder with Kali NetHunter modifications support.

## Contents

- [zero\_kernel](#zero_kernel)
  - [Contents](#contents)
  - [**Disclaimer**](#disclaimer)
  - [Description](#description)
  - [Kernel Features](#kernel-features)
  - [Supported ROMs](#supported-roms)
  - [ROM Artifacts in Releases](#rom-artifacts-in-releases)
  - [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Kernel](#kernel)
    - [Assets](#assets)
    - [Bundle](#bundle)
  - [Examples](#examples)
  - [See also](#see-also)
  - [Credits](#credits)

## **Disclaimer**

> [!IMPORTANT]
> **This kernel is made for educational purposes only.**
>
> **I am not responsible for anything that may or may not happen to your device by installing any custom ROMs, kernels and/or any other forms of software.**
>
> **Anything you do with this kernel and your device you do at your own risk. By using it, you take the responsibility upon yourself and in case of any issue you are not to blame me or other related contributors.**

## Description

Technically speaking, the codebase of this project is an extensive wrapper automating the entire Android kernel build process, starting from kernel source collection and ending with artifact packaging.

The key goal is to modify the kernel in such a way that enables unique features of [Kali NetHunter](https://www.kali.org/docs/nethunter) — a ROM layer designed to add extended functionality for penetration testing in a mobile form factor.

The architecture of this wrapper is ~~trying to be~~ as modular as possible, making it a little easier to add support for new devices.

## Kernel Features

The kernel has the following features:

- Kali NetHunter support;
- RTL8812/21AU + RTL8814AU + RTL8187 Wi-Fi drivers;
- packet injection support for internal Wi-Fi chipset;
- optional KernelSU support.

## Supported ROMs

For **OnePlus 5/T** devices:

- 4.4 Linux kernel version:
  - LineageOS;
  - ParanoidAndroid;
  - x_kernel supported (universal)*.
- 4.14 Linux kernel version:
  - ParanoidAndroid (unofficial & testing);
  - x-ft_kernel supported (universal)**.

\* -- this is mostly relevant to ROMs based on LineageOS; however, technically speaking, this includes ParanoidAndroid as well, which makes x_kernel-based builds universal.

\** -- this, **in theory**, is relevant to all 4.14-based ROMs for this device in existence.

## ROM Artifacts in Releases

> [!NOTE]
> The contents of each release include ROM builds compatible with corresponding kernel builds. These ROM files are **unmodified and mirrored from official sources**.

This can be verified via the checksums, which should be identical to the ones presented on the ROM project's official web page.

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

> [!WARNING]
> Because of how *specific* Linux kernel source is, building it on Windows even with Docker might be challenging.

To run this tool in a `local` environment, you will need:

- a Debian-based Linux distribution (other types of distros are untested);
- a few [packages](Dockerfile#L15) installed in your system.

You will also need to configure your Python installation, including some of the packages installation:

```sh
python3 -m pip install poetry
python3 -m poetry install --no-root
export PYTHONPATH=$(pwd)
```

### Kernel

Kernel build process can be launched using the `kernel` subcommand of the wrapper.

```help
$ python3 wrapper kernel --help
usage: wrapper kernel [-h] --build-env {local,docker,podman} --base
                      {los,pa,x,aosp} --codename CODENAME --lkv LKV [-c]
                      [--clean-image] [--log-level {normal,verbose,quiet}]
                      [-o OUTLOG] [--ksu]

options:
  -h, --help            show this help message and exit
  --build-env {local,docker,podman}
                        select build environment
  --base {los,pa,x,aosp}
                        select a kernel base for the build
  --codename CODENAME   select device codename
  --lkv LKV             select Linux Kernel Version
  -c, --clean           don't build anything, only clean kernel directories
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
usage: wrapper assets [-h] --build-env {local,docker,podman} --base
                      {los,pa,x,aosp} --codename CODENAME --chroot
                      {full,minimal} [--rom-only] [--clean-image] [--clean]
                      [--log-level {normal,verbose,quiet}] [-o OUTLOG] [--ksu]

options:
  -h, --help            show this help message and exit
  --build-env {local,docker,podman}
                        select build environment
  --base {los,pa,x,aosp}
                        select a kernel base for the build
  --codename CODENAME   select device codename
  --chroot {full,minimal}
                        select Kali chroot type
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
usage: wrapper bundle [-h] --build-env {local,docker,podman} --base
                      {los,pa,x,aosp} --codename CODENAME --lkv LKV
                      --package-type {conan,slim,full} [--conan-upload]
                      [--clean-image] [--log-level {normal,verbose,quiet}]
                      [-o OUTLOG] [--ksu]

options:
  -h, --help            show this help message and exit
  --build-env {local,docker,podman}
                        select build environment
  --base {los,pa,x,aosp}
                        select a kernel base for the build
  --codename CODENAME   select device codename
  --lkv LKV             select Linux Kernel Version
  --package-type {conan,slim,full}
                        select package type of the bundle
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

**(Recommended)** Build kernel and collect ROM via Docker:

```sh
python3 wrapper bundle --build-env=docker --base=los --codename=dumpling --lkv=4.4 --package-type=slim
```

Build kernel locally:

```sh
python3 wrapper kernel --build-env=local --base=los --codename=dumpling --lkv=4.4
```

Collect all of the assets locally:

```sh
python3 wrapper assets --build-env=local --base=los --codename=dumpling --package-type=full
```

## See also

- [FAQ](docs/FAQ.md);
- [TODO List](docs/TODO.md);
- [Kernel Flashing Instructions](docs/FLASHING.md).

## Credits

- [x_kernel_oneplus_msm8998](https://github.com/ederekun/x_kernel_oneplus_msm8998): OnePlus 5/T kernel with many optimizations and improvements;
- [x-ft_kernel_oneplus_msm8998](https://github.com/ederekun/x-ft_kernel_oneplus_msm8998): 4.14-based variation of x_kernel;
- [4.14-kernel-oneplus-msm8998](https://github.com/roberto-sartori-gl/4.14-kernel-oneplus-msm8998): a base of 4.14 kernels for OnePlus 5/T, with KernelSU patches;
- [kali-nethunter-kernel](https://gitlab.com/kalilinux/nethunter/build-scripts/kali-nethunter-kernel): official kernel patches from Kali NetHunter project.
