import pygame
from dataclasses import dataclass
from pygame.sprite import Sprite, Rect

from esper import Processor
from .datacl import GameObject
from . import env

import os


def load_sprites(name):
    surfaces = []
    path = os.path.join("assets", "images", name)
    for f in sorted(os.listdir(path)):
        if os.path.isfile(os.path.join(path, f)) and "png" in f:
            sf = pygame.image.load(os.path.join(path, f)).convert_alpha()
            if name == "inflator":
                sf = pygame.transform.smoothscale(sf, (env.LEM_WIDTH * 2, env.LEM_HEIGHT * 2)).convert_alpha()
            elif name == "deflator":
                sf = pygame.transform.smoothscale(sf, (int(env.LEM_WIDTH * 0.5), int(env.LEM_HEIGHT * 0.5))).convert_alpha()
            else:
                sf = pygame.transform.smoothscale(sf, (env.LEM_WIDTH, env.LEM_HEIGHT)).convert_alpha()
            surfaces.append(sf)
    return surfaces


def load_hud():
    hud = {}
    path = os.path.join("assets", "images", "hud")
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and "png" in f:
            sf = pygame.image.load(os.path.join(path, f)).convert_alpha()
            if "inventory" in f:
                wf = env.SCR_WIDTH / sf.get_width()
                sf = pygame.transform.smoothscale(sf, (env.SCR_WIDTH, int(sf.get_height() * wf))).convert_alpha()
            hud[f.split(".")[0]] = sf
    return hud

def load_icons():
    icons = {}
    path = os.path.join("assets", "images", "icons")
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and "png" in f:
            sf = pygame.image.load(os.path.join(path, f)).convert_alpha()
            icons[f.split(".")[0]] = sf
    return icons


class GraphicsLoader(dict):
    def __init__(self):
        self["walk"] = load_sprites("walk")
        self["inflator"] = load_sprites("inflator")
        self["deflator"] = load_sprites("deflator")
        self["climb"] = load_sprites("climb")
        self["cover"] = load_sprites("cover")
        self["death"] = load_sprites("death")
        self["idle"] = load_sprites("idle")
        self["fall"] = load_sprites("fall")
        self["hud"] = load_hud()
        self["icons"] = load_icons()


@dataclass
class SpriteComponent:
    sprite: Sprite
    current_anim_index: int = 0

    @property
    def rect(self):
        return self.sprite.rect

    @rect.setter
    def rect(self, value):
        raise Exception("Set the GameObject instead!")

    @property
    def image(self):
        return self.sprite.image

    @image.setter
    def image(self, value):
        self.sprite.image = value


class SpriteProcessor(Processor):
    def __init__(self):
        super(SpriteProcessor, self).__init__()

    def process(self, scene, delta):
        """
        Update pygame sprite rects to match the game object's size and location
        """
        entities = self.world.get_components(GameObject, SpriteComponent)
        for eid, (game_object, sprite_comp) in entities:
            sprite = sprite_comp.sprite
            sprite.rect = Rect(game_object.pos, game_object.size)

