# s0nh — LineageOS + NetHunter Kernel

## **Disclaimer**

**This kernel is made for educational purposes only.**

**I am not responsible for anything that may happen to your device by installing any custom ROMs and/or kernels.**

**Anything you do with this kernel you do at your own risk. By using it, you take the responsibility upon yourself and in case of any issue you are not to blame me or other related contributors.**


## **If you're seeing this on GitHub**

If you are seeing this project on **GitHub** -- please note that you are viewing only **a mirror**.

Project development is mainly done on **GitLab**.


## **Kernel Features**

The kernel has the following features:

- Kali NetHunter support;
- RTL8812AU Wi-Fi drivers.


## **Usage**

The custom build wrapper consists of 3 main parts:

- kernel builder;
- assets collector;
- kernel + assets bundler.

```help
$ python3 wrapper --help
usage: wrapper [-h] [--clean] {kernel,assets,bundle} ...

A custom wrapper for the s0nh kernel.

positional arguments:
  {kernel,assets,bundle}
    kernel              build the kernel
    assets              collect assets
    bundle              build the kernel + collect assets

optional arguments:
  -h, --help            show this help message and exit
  --clean               clean the root directory
```


### **Prerequisites**

To launch the tool you need to make sure you have the following:

- Python 3.6+;
- a Debian-based operating system AND/OR Docker installation.

You will also need a few Python packages. To install them, use:

```sh
python3 -m pip install -r requirements.txt
```

### **Kernel**

Kernel build process can be launched by using the `python3 wrapper kernel <arguments>` command.

For more options you can refer to the help message below.

```help
$ python3 wrapper kernel --help
usage: wrapper kernel [-h] [-c] [--clean-docker] [--log-level {normal,verbose,quiet}] {local,docker} losversion codename

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  codename              select device codename

optional arguments:
  -h, --help            show this help message and exit
  -c, --clean           don't build anything, just clean the environment
  --clean-docker        remove Docker image from the host machine after build
  --log-level {normal,verbose,quiet}
                        select log level
```

### **Assets**

As mentioned, there is also an asset downloader, which can collect latest versions of LineageOS ROM, TWRP, Magisk and it's modules, Kali Chroot etc.

```help
$ python3 wrapper assets --help
usage: wrapper assets [-h] [--extra-assets EXTRA_ASSETS] [--clean-docker] [--clean] [--log-level {normal,verbose,quiet}] {local,docker} losversion codename {full,minimal}

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  codename              select device codename
  {full,minimal}        select Kali chroot type

optional arguments:
  -h, --help            show this help message and exit
  --extra-assets EXTRA_ASSETS
                        select a JSON file with extra assets
  --clean-docker        remove Docker image from the host machine after build
  --clean               autoclean 'assets' folder if it exists
  --log-level {normal,verbose,quiet}
                        select log level
```

### **Bundle / Conan packaging**

There is an option named `bundle` which combines build artifacts of both `kernel` and `assets` modules into a single Conan component.

This is especially useful for linking the kernel version with the appropriate LineageOS ROM version.

There are cases when an old kernel version is used with the newer ROM version (adapted for the *newer* version of kernel). Such cases can ultimately lead to your system working improperly or breaking down completely, which is why it is important to use a specific kernel build with a corresponding ROM build.

```help
$ python3 wrapper bundle --help
usage: wrapper bundle [-h] [--conan-cache] [--conan-upload] [--clean-docker] [--log-level {normal,verbose,quiet}] {local,docker} losversion codename

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  codename              select device codename

optional arguments:
  -h, --help            show this help message and exit
  --conan-cache         mount Conan cache into Docker container
  --conan-upload        upload Conan packages to remote
  --clean-docker        remove Docker image from the host machine after build
  --log-level {normal,verbose,quiet}
                        select log level
```

## **See also**

- [TODO List](documentation/TODO.md);
- [Kernel Flashing Instructions](documentation/FLASHING.md).
