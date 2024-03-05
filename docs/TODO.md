# TODO

## Kernel features

- [x] add monitor mode support for internal Wi-Fi chipset (with Wi-Fi packet injection);
- [ ] add DM-Verity and Force Encrypt disabler;
- [x] add KernelSU support;
- [ ] add DriveDroid(-like) support.

## Build process features

- [x] add an asset downloader (ROM, Magisk, etc.);
- [x] add CI/CD pipelines;
- [x] add option to save logs to a file;
- [x] add option to build in Docker container;
- [x] add multidevice support, with appropriate manifest;
- [x] improve log level setting throughout all stages of the build;
- [x] improve file/directory cleaning mechanism in a form of a dedicated module;
- [x] improve Clang download mechanism;
- [x] add build counter mechanism for CI/CD pipelines;
- [ ] add published Conan package validator;
- [x] add codename specific elements to final kernel zip;
- [x] add a simpler and slimer bundle creator (kernel+ROM);
- [x] add return types to functions;
- [x] add requirements.txt for pip;
- [x] add proper OS detection for preventing local builds in unsupported systems;
- [x] add static analysis for the wrapper;
- [x] add a single-point manifest with main info on the tool;
- [x] improve documentation;
- [x] apply OOP paradigm;
- [x] switch to Poetry for dependency management;
- [ ] create a commit-based lockfile system for reproducible kernel builds;
- [x] switch to `pathlib`;
- [ ] switch to `raise` instead of `sys.exit`;
- [x] add a FAQ page;
- [x] refactor Docker/Podman command formation;
- [ ] refactor logging mechanism;
- [x] fix Podman usage (.dockerignore);
- [ ] dedicate kernel source patchers as separate modules (LineageOS, AOSP, AOSPA etc);
- [x] add a separate method for multiline patching in files;
- [ ] make kernel building and assets collection processes asynchronous when launching the `bundle` option;
- [x] add a dataclass for wrapper's arguments;
- [x] add PA ROM support;
- [ ] add a GH workflow for checking PRs;
- [x] decompose `run()` method in `ContainerEngine`;
- [x] skip building Docker/Podman image if it's already present in local cache;
- [x] for containerized build, download the contents of manifests during image build;
- [ ] add system app debloater;
- [x] add a new argument responsible for Linux kernel version selection;
- [x] add 4.14 Linux kernel version builds;
- [ ] decompose `run` methods into separate methods as much as possible;
- [x] switch to pydantic;
- [ ] new device support: OP9;
- [ ] add type checks with pyright;
- [ ] add unit tests with coverage checks;
- [ ] move device-specific modifications into appropriate folder with custom Modificator (sub)classes;
- [ ] switch to `__enter__` and `__exit__` Python's magic methods for container engines;
- [ ] switch to `exec` commands for Docker and Podman instead of a single `run` command;
- [ ] replace `ccmd.launch()` to just `launch()` (or any other name);
- [ ] embed newlines usage (from both sides) into `messages` functions as arguments;
- [ ] add tests on cases of custom wrapper edge case exits (kernel build on Windows, ROM-only asset collection for a ROM-universal kernel etc.);
- [ ] break down (or create inheritance from) KernelBuilder into LineageOsKernelBuilder, ParanoidAndroidKernelBuilder, XKernelBuilder etc;
- [ ] investigate project restructuring to avoid circular import;
- [ ] consider creating a separate "errors" subpackage for all errors;
- [ ] add GKI kernels support;
- [ ] separate "standard" kernel building from NetHunter-specific modifications.
