# TODO

## Kernel features

### Done

- [x] add monitor mode support for internal Wi-Fi chipset (with Wi-Fi packet injection);
- [x] add KernelSU support.
- [x] add DM-Verity and Force Encrypt disabler.

### Left

- [ ] add DriveDroid(-like) support.

## Build process features

### Done

- [x] add an asset downloader (ROM, Magisk, etc.);
- [x] add CI/CD pipelines;
- [x] add option to save logs to a file;
- [x] add option to build in Docker container;
- [x] add multidevice support, with appropriate manifest;
- [x] improve log level setting throughout all stages of the build;
- [x] improve file/directory cleaning mechanism in a form of a dedicated module;
- [x] improve Clang download mechanism;
- [x] add build counter mechanism for CI/CD pipelines;
- [x] add codename specific elements to final kernel zip;
- [x] add a simpler and slimer bundle creator (kernel+ROM);
- [x] add return types to functions;
- [x] add requirements.txt for pip;
- [x] add proper OS detection for preventing local builds in unsupported systems;
- [x] add static analysis for the wrapper;
- [x] add a single-point manifest with main info on the tool;
- [x] improve documentation;
- [x] apply OOP paradigm;
- [x] switch to uv for dependency management;
- [x] switch to `pathlib`;
- [x] add a FAQ page;
- [x] refactor Docker/Podman command formation;
- [x] fix Podman usage (.dockerignore);
- [x] add a separate method for multiline patching in files;
- [x] add a dataclass for wrapper's arguments;
- [x] add PA ROM support;
- [x] decompose `run()` method in `ContainerEngine`;
- [x] skip building Docker/Podman image if it's already present in local cache;
- [x] for containerized build, download the contents of manifests during image build;
- [x] add a new argument responsible for Linux kernel version selection;
- [x] add 4.14 Linux kernel version builds;
- [x] decompose `run` methods into separate methods as much as possible;
- [x] switch to pydantic;
- [x] add type checks with pyright;
- [x] add unit tests with coverage checks;
- [x] switch to `__enter__` and `__exit__` Python's magic methods for container engines.

### Left

- [ ] add published Conan package validator;
- [ ] create a commit-based lockfile system for reproducible kernel builds;
- [ ] dedicate kernel source patchers as separate modules (LineageOS, AOSP, AOSPA etc);
- [ ] make kernel building and assets collection processes asynchronous when launching the `bundle` option;
- [ ] add a GitHub workflow for checking PRs;
- [ ] add system app debloater;
- [ ] move device-specific modifications into appropriate folder with custom Modificator (sub)classes;
- [ ] switch to `exec` commands for Docker and Podman instead of a single `run` command;
- [ ] replace `ccmd.launch()` to just `launch()` (or any other name);
- [ ] embed newlines usage (from both sides) into `messages` functions as arguments;
- [ ] add tests on cases of custom wrapper edge case exits (kernel build on Windows, ROM-only asset collection for a ROM-universal kernel etc.);
- [ ] break down (or create inheritance from) KernelBuilder into LineageOsKernelBuilder, ParanoidAndroidKernelBuilder, XKernelBuilder etc;
- [ ] investigate project restructuring to avoid circular import;
- [ ] consider creating a separate "errors" subpackage for all errors;
- [ ] add GKI kernels support;
- [ ] use logging facility for logs.
