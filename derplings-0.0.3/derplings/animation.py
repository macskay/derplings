from dataclasses import dataclass
import pygame.transform
import pygame.image

from . import env
from .gfx import SpriteComponent

from esper import Processor


@dataclass
class FacingComponent:
    direction: float = 0


class AnimationComponent:
    delta: int = 0
    index: int = 0
    threshold: dict = {"walk": env.LEM_WALK_ANIM_SPEED, "death": env.LEM_DEATH_ANIM_SPEED, "idle": 0, "fall": 0, "inflator": env.LEM_WALK_ANIM_SPEED, "deflator": env.LEM_WALK_ANIM_SPEED, "climb": env.LEM_WALK_ANIM_SPEED, "cover": 0}
    anim_set: str = "fall"
    mirror: bool = False
    loop: dict = {"walk": True, "death": False, "idle": True, "fall": True, "inflator": True, "deflator": True, "climb": True, "cover": True}
    stop: bool = False

    def reset_animation(self):
        self.delta = 0
        self.index = 0

    def change_animation(self, anim_set):
        self.anim_set = anim_set
        self.reset_animation()


class AnimationProcessor(Processor):
    def __init__(self):
        super(AnimationProcessor, self).__init__()

    def process(self, scene, delta):
        query = (AnimationComponent, SpriteComponent)
        entities = list(self.world.get_components(*query))

        for eid, (anim, sprite) in entities:
            if anim.anim_set not in scene.assets.keys():
                return

            anim.delta += delta
            if anim.delta > anim.threshold[anim.anim_set] and not anim.stop:
                if anim.loop[anim.anim_set]:
                    anim.index %= len(scene.assets[anim.anim_set])
                elif anim.index == len(scene.assets[anim.anim_set]):
                    anim.index = -1
                    anim.stop = True
                anim.delta = 0

                sprite.sprite.image = scene.assets[anim.anim_set][anim.index]

                if anim.mirror:
                    sprite.sprite.image = pygame.transform.flip(sprite.sprite.image, True, False)
                anim.index += 1
