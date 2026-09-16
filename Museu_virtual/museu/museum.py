"""Composição da aplicação do Museu Virtual.

A classe pública continua sendo MuseuVirtual3D, mas sua implementação foi
separada em mixins por responsabilidade.
"""
from .scene import SceneMixin
from .navigation import NavigationMixin
from .animation import AnimationMixin
from .renderer import RendererMixin
from .ui import UIMixin
from .app import AppMixin


class MuseuVirtual3D(
    SceneMixin,
    NavigationMixin,
    AnimationMixin,
    RendererMixin,
    UIMixin,
    AppMixin,
):
    """Fachada principal que reúne os módulos da aplicação."""
    pass
