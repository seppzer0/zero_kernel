from conans import ConanFile


class S0nhConan(ConanFile):
    name = "zero"
    version = "0.4.0"
    author = "seppzer0"
    url = "https://gitlab.com/api/v4/projects/40803264/packages/conan"
    description = "An Android kernel with Kali NetHunter functionality."
    topics = ("zero_kernel", "kali-nethunter")
    settings = None
    options = {
                "rom": ("los", "pa", "x"),
                "chroot": ("minimal", "full"),
                "codename": ("dumpling", "cheeseburger")
              }

    def export_sources(self):
        self.copy("*", src="source", dst=".")

    def build(self):
        cmd = "python3 wrapper kernel local {0} {1} &&"\
              "python3 wrapper assets local {0} {1} {2} --clean"\
              .format(
                  self.options.rom,
                  self.options.codename,
                  self.options.chroot
              )
        print(f"[cmd] {cmd}")
        self.run(cmd)

    def package(self):
        # package built kernel with collected assets
        self.copy("*.zip", src="kernel", dst="kernel", keep_path=False)
        self.copy("*", src="assets", dst="assets")
