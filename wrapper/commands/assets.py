from wrapper.modules import AssetsCollector


class AssetsCommand(AssetsCollector):
    """A command responsible for launching the 'assets_collector' core module directly."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
