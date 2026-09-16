"""Ponto de montagem da aplicação: reúne todos os mixins em uma única classe."""
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
    """Classe principal do museu — combina cena, navegação, animação, renderização, UI e loop de eventos."""
    pass
