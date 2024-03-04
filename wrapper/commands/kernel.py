from wrapper.modules import KernelBuilder


class KernelCommand(KernelBuilder):
    """A command responsible for launching the 'kernel_builder' core module directly."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
