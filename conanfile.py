from conans import ConanFile


class ZeroKernelConan(ConanFile):
    name = "zero"
    version = "0.4.1"
    author = "seppzer0"
    url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
    description = "An Android kernel with Kali NetHunter functionality."
    topics = ("zero_kernel", "kali-nethunter", "nethunter")
    settings = None
    options = {
                "base": ("los", "pa", "x", "aosp"),
                "chroot": ("minimal", "full"),
                "codename": ("dumpling", "cheeseburger")
              }

    def export_sources(self):
        self.copy("*", src="source", dst=".")

    def build(self):
        shared_args = "--build-env=local --base={} --codename={} --chroot={}"\
                      .format(
                        self.options.base,
                        self.options.codename,
                        self.options.chroot
                       )
        cmd = "python3 wrapper kernel {0} &&"\
              "python3 wrapper assets {0} --clean"\
              .format(shared_args)
        print(f"[cmd] {cmd}")
        self.run(cmd)

    def package(self):
        # package built kernel with collected assets
        self.copy("*.zip", src="kernel", dst="kernel", keep_path=False)
        self.copy("*", src="assets", dst="assets")
