# LineageOS + NetHunter Kernel For OnePlus 5/T

## **Disclaimer**

**This kernel is made for educational purposes only.**

**I am not responsible for anything that may happen to your device by installing any custom ROMs and/or kernels.**

**Anything you do with this kernel you do at your own risk. By using it, you take the responsibility upon yourself and in case of any issue you are not to blame me or other related contributors.**

<br>

## **If you're seeing this on GitHub**

If you are seeing this project on **GitHub** -- please take a note that you are viewing only **a mirror**.

Project development is mainly done on **GitLab**.


<br>

## **Kernel Features**

The kernel has the following features:

- Kali NetHunter support;
- RTL8812AU Wi-Fi drivers.

<br>

## **Usage**

The custom build wrapper consists of 3 main components:

- kernel builder;
- assets collector;
- kernel + assets bundler.

```help
$ python3 wrapper --help
usage: [-h] {kernel,assets,bundle} ...

A custom wrapper for the s0nh kernel.

positional arguments:
  {kernel,assets,bundle}
    kernel              build the kernel
    assets              collect assets
    bundle              build the kernel + collect assets

optional arguments:
  -h, --help            show this help message and exit
```

<br>

### **Kernel**

The kernel build process can be launched by simply using the `python3 wrapper kernel <arguments>` command.

For more options you can refer to the help message below.

```help
$ python3 wrapper kernel --help
usage: wrapper kernel [-h] [-c] [--clean-docker] [--log-level {normal,verbose,quiet}] {local,docker} losversion {dumpling,cheeseburger}

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  {dumpling,cheeseburger}
                        select device codename

optional arguments:
  -h, --help            show this help message and exit
  -c, --clean           don't build anything, just clean the environment
  --clean-docker        remove Docker image from the host machine after build
  --log-level {normal,verbose,quiet}
                        select log level
```

<br>

### **Assets**

As mentioned, there is also an asset downloader, which can download latest versions of LineageS ROM, TWRP, Magisk and it's modules, Kali Chroot etc.

```help
$ python3 wrapper assets --help
usage: wrapper assets [-h] [--extra-assets EXTRA_ASSETS] [--clean-docker] [--clean]
                      [--log-level {normal,verbose,quiet}]
                      {local,docker} losversion {dumpling,cheeseburger} {full,minimal}

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  {dumpling,cheeseburger}
                        select device codename
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

<br>

### **Bundle / Conan packaging**

There is an option named `bundle` which combines the build artifacts of both `kernel` and `assets` modules into a single Conan component.

This is especially useful for linking the kernel version with the appropriate LineageOS ROM version, as there are cases when an old kernel version can used along the newer ROM version (adapted for the *new* kernel), which ultimately leads to you system working improperly of breaking down completely.

```help
$ python3 wrapper bundle --help
usage: wrapper bundle [-h] [--conan-cache] [--conan-upload] [--clean-docker]
                      [--log-level {normal,verbose,quiet}]
                      {local,docker} losversion {dumpling,cheeseburger}

positional arguments:
  {local,docker}        select whether this is a 'local' or 'docker' build
  losversion            select LineageOS version
  {dumpling,cheeseburger}
                        select device codename

optional arguments:
  -h, --help            show this help message and exit
  --conan-cache         mount Conan cache into Docker container
  --conan-upload        upload Conan packages to remote
  --clean-docker        remove Docker image from the host machine after build
  --log-level {normal,verbose,quiet}
                        select log level
```

<br>

## **See also**

- [TODO List](documentation/TODO.md);
- [Kernel Flashing Instructions](documentation/FLASHING.md).
