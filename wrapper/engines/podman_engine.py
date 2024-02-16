from .template_container_engine import TemplateContainerEngine


class PodmanEngine(TemplateContainerEngine):
    """Podman engine.
    
    :param benv: Build environment.
    """

    benv: str = "podman"
