import os
from . import env
from .gfx import SpriteComponent
from .inventory import InventoryComponent
from dataclasses import dataclass
from esper import Processor
from itertools import count
from pygame.font import Font
from pygame.sprite import Sprite
from typing import Any
from pygame import Rect
from pygame import Color
from .derpling import DerplingCountComponent

LABEL_DATA = [
    "ladder",
    "umbrella",
    "trampoline",
    "stop_sign",
    "jetpack",
    "rocket",
    "inflator",
    "deflator",
    "tnt",
]


@dataclass
class LabelComponent:
    antialias: bool = True
    bg_alpha: int = 0
    bg_color: Color = Color("black")
    bold: bool = False
    fg_alpha: int = 255
    fg_color: Color = Color("white")
    font_file: str = "OstrichSans-Heavy.otf"
    font_size: int = 12
    is_dirty: bool = True
    italic: bool = False
    _text: str = "Label"

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self.is_dirty = True
        self._text = value


@dataclass
class LabelBindingComponent:
    bound_entity_id: int
    bound_component: Any
    bound_property: str


class LabelProcessor(Processor):
    def process(self, scene, delta):
        labels = self.world.get_components(LabelComponent, SpriteComponent)
        for label_id, (label, sprite) in labels:
            if label.is_dirty:
                self.update_sprite(label, sprite)

    def update_sprite(self, label, sprite):
        path = os.path.join("assets", "fonts", label.font_file)
        font = Font(path, label.font_size)
        font.set_bold(label.bold)
        font.set_italic(label.italic)
        label.fg_color.a = label.fg_alpha
        label.bg_color.a = label.bg_alpha
        sprite.image = font.render(
            label.text, label.antialias, label.fg_color, label.bg_color
        ).convert_alpha()
        sprite.sprite.rect.size = sprite.image.get_size()
        label.is_dirty = False


class LabelBindingProcessor(Processor):
    def process(self, scene, delta):
        bindings = self.world.get_components(LabelBindingComponent, LabelComponent)
        for binding_id, (binding, label) in bindings:
            bound_component = self.world.component_for_entity(
                binding.bound_entity_id, binding.bound_component
            )
            if hasattr(bound_component, binding.bound_property):
                value = getattr(bound_component, binding.bound_property)
            else:
                value = "???"
            label.text = str(value)


class HUDBuilder:
    INVENTORY_FONT_SIZE = 72

    def __init__(self, topleft, world, sprite_group, assets):
        self.sprite_group = sprite_group
        self.topleft = topleft
        self.world = world
        self.inventory_id = 0
        self.assets = assets

    def build(self):
        self.build_hud()

    def build_hud(self):
        inventory_sprite = Sprite()
        inventory_sprite.image = self.assets["hud"]["inventory"]
        inventory_sprite.rect = inventory_sprite.image.get_rect()
        inventory_sprite.rect.topleft = self.topleft
        self.sprite_group.add(inventory_sprite, layer=2)
        self.inventory_id = self.world.create_entity(
            InventoryComponent(), SpriteComponent(inventory_sprite)
        )

        offset_generator = count(self.topleft[0], env.SCR_WIDTH // 10)
        for offset, bound_property in zip(offset_generator, LABEL_DATA):
            self.create_quantity_label(offset, bound_property)
        derp_count = self.world.create_entity(DerplingCountComponent())
        offset = next(offset_generator)
        self.create_quantity_label(
            offset - 130,
            "derpling_count",
            component=DerplingCountComponent,
            entity_id=derp_count,
        )

    def create_quantity_label(
        self, offset_x, bound_property, component=InventoryComponent, entity_id=None
    ):
        bg_color = Color("black")
        bg_color.r = 128
        bg_color.g = 83
        bg_color.b = 21
        bg_color.a = 0

        fg_color = Color("black")
        fg_color.r = 255
        fg_color.g = 219
        fg_color.b = 170
        fg_color.a = 255

        bound_label = LabelComponent()
        bound_label.font_size = self.INVENTORY_FONT_SIZE
        bound_label.bg_color = bg_color
        bound_label.fg_color = fg_color

        if entity_id is None:
            entity_id = self.inventory_id

        bound_sprite = Sprite()
        self.sprite_group.add(bound_sprite, layer=3)
        bound_sprite.rect = Rect(offset_x + 75, self.topleft.y + 70, 0, 0)
        label_binding = LabelBindingComponent(entity_id, component, bound_property)
        self.world.create_entity(
            bound_label, SpriteComponent(bound_sprite), label_binding
        )
