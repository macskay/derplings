import pygame
import argparse
import logging
import os.path
from zkit.scenes import Game

from . import env
from .game import TowerScene
from .imagescene import ImageScene
from .particles import ParticleTestScene

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--map", type=str, help="Which Map to load", default="map.tmx"
    )
    parser.add_argument(
        "-d", "--debug", help="Activate Debug Mode", default=False, action="store_true"
    )
    return parser.parse_args()


def bootstrap_game():
    logging.basicConfig(level=logging.ERROR)

    pygame.mixer.quit()
    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    pygame.mixer.music.load(os.path.join("assets", "music", "derplings.ogg"))
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(loops=-1)

    main_surface = pygame.display.set_mode((env.SCR_WIDTH, env.SCR_HEIGHT))

    game = Game(60, main_surface)
    game.register_scene(ImageScene("title", "title.png", "instructions"))
    game.register_scene(ImageScene("instructions", "instructions.png", "tower"))
    game.register_scene(ParticleTestScene())
    game.register_scene(TowerScene(parse_args()))
    # game.register_scene(ParticleTestScene())
    game.push_scene("title")
    return game
