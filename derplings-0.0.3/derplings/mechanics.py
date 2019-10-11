import pygame
from dataclasses import dataclass

from esper import Processor
from .datacl import GameObject
from .animation import AnimationComponent
from .gfx import SpriteComponent
from . import env
from .movement import StopWatchComponent
from planar import Point, Vec2
from .particles import ParticleGeneratorComponent
from .particles import ParticleEffect
from .datacl import PlatformComponent, WeakPlatformMarker


@dataclass
class LadderComponent:
    """Marker class for ladder"""

    in_use: bool = False
    pass


@dataclass
class TNTComponent:
    explode_delay: int = 3000  # MS


@dataclass
class BlastRadiusComponent:
    pos: Point
    size: int


class TNTProcessor(Processor):
    def process(self, scene, delta):
        tnts = self.world.get_components(TNTComponent, StopWatchComponent, GameObject, SpriteComponent)
        for tnt_id, (tnt, stop_watch, game_object, sprite) in tnts:
            if stop_watch.elapsed_ms >= tnt.explode_delay:
                sprite.sprite.kill()

                self.world.delete_entity(tnt_id)
                explode_pos = Point(
                    (game_object.pos.x + game_object.w / 2),
                    game_object.pos.y + game_object.h / 2,
                )
                self.world.create_entity(
                    ParticleGeneratorComponent.create_effect(
                        explode_pos, ParticleEffect.MEDIUM_EXPLOSION
                    )
                )

                self.world.create_entity(
                    ParticleGeneratorComponent.create_effect(
                        explode_pos, ParticleEffect.SMOKE
                    )
                )

                scene.sounds["sounds"]["explosion01"].play(
                    loops=0, maxtime=0, fade_ms=0
                )

                self.world.create_entity(BlastRadiusComponent(explode_pos, 64))


class BlastProcessor(Processor):
    def process(self, scene, delta):
        blasts = self.world.get_component(BlastRadiusComponent)
        platforms = self.world.get_components(GameObject, SpriteComponent, WeakPlatformMarker)

        for _, blast in blasts:
            for platform_id, (platform, sprite, _) in platforms:
                blast_rect = pygame.Rect(blast.pos, (blast.size, blast.size))
                if blast_rect.colliderect(platform.rect):
                    self.world.delete_entity(platform_id)
                    sprite.sprite.kill()

