import pygame
from dataclasses import dataclass

from pygame import Surface
from esper import Processor
from .datacl import GameObject
from .derpling import DerplingState
from .gfx import SpriteComponent
from . import env

from planar import Vec2, Point


@dataclass
class CameraComponent:
    cam_speed: float = 64.0
    free_cam: bool = True
    index: int = 0


class CameraProcessor(Processor):

    def __init__(self):
        super(CameraProcessor, self).__init__() 
        self.index = 0

    def process(self, scene, delta):
        if scene.game_end:
            return
        entities = self.world.get_components(GameObject, CameraComponent, SpriteComponent)
        derplings = self.world.get_components(GameObject, DerplingState)

        for eid, (game_object, camera_object, sprite) in entities:
            state = pygame.key.get_pressed()
            motion = Vec2.polar(90, env.GRID_SIZE)
            map_height = scene.tiled_data.height * 32
            new_pos = None

            if state[pygame.K_DOWN]:
                new_pos = game_object.pos + motion
                camera_object.free_cam = True
                sprite.sprite.image = Surface(sprite.rect.size).convert_alpha()
                sprite.sprite.image.fill((0, 0, 0, 0))
            elif state[pygame.K_UP]:
                new_pos = game_object.pos - motion
                camera_object.free_cam = True
                sprite.sprite.image = Surface(sprite.rect.size).convert_alpha()
                sprite.sprite.image.fill((0, 0, 0, 0))
            elif not camera_object.free_cam:
                cam_derpling = derplings[camera_object.index]

                new_pos = Point(
                    cam_derpling[1][0].pos.x,
                    cam_derpling[1][0].pos.y - 8,
                )

                game_object.pos = new_pos
                scene.sprite_group.center(game_object.pos)


            if new_pos is not None:
                if 0 <= new_pos.y <= map_height:
                    game_object.pos = new_pos
                    scene.sprite_group.center(game_object.pos)
