import pygame.mixer
from dataclasses import dataclass

import os


def load_sounds(name):
    sounds = {}
    path = os.path.join("assets", name)
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and ".wav" in f:
            sf = pygame.mixer.Sound(os.path.join(path, f))
            sf.set_volume(0.3)
            sounds[f.split(".")[0]] = sf
    return sounds


class SoundLoader(dict):
    def __init__(self):
        self["sounds"] = load_sounds("sounds")
        self["music"] = load_sounds("music")


@dataclass
class SoundComponent:
    """ MarkerClass for Sounds """
