from .template_container_engine import TemplateContainerEngine


class PodmanEngine(TemplateContainerEngine):
    """Podman engine."""

    benv: str = "podman"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
