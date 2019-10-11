from dataclasses import dataclass

from esper import Processor
from planar import Point

from . import env
from .datacl import Facing
from .datacl import GameObject
from .derpling import DerplingState
from .gfx import SpriteComponent


@dataclass
class SpawnComponent:
    amount: int = env.SPAWN_AMOUNT
    active: bool = env.SPAWN_ACTIVE
    spawn_time: int = env.SPAWN_TIME  # in ms
    current: int = 0
    spawn_free: bool = False


class SpawnProcessor(Processor):
    def __init__(self):
        super(SpawnProcessor, self).__init__()
        self.delta = 0

    def process(self, scene, delta):
        self.delta += delta
        spawners = self.world.get_components(
            GameObject, SpawnComponent, SpriteComponent
        )
        for eid, (game_object, spawner, spawn_sprite) in spawners:
            if spawner.active:
                if spawner.current < spawner.amount:
                    if self.delta > spawner.spawn_time:
                        spawn_pos = Point(
                            game_object.pos.x
                            + spawn_sprite.sprite.rect.w // 2
                            - env.LEM_WIDTH // 2,
                            game_object.pos.y,
                        )
                        scene.create_derpling(
                            Point(*spawn_pos),
                            Facing.RIGHT,
                            imprisoned=not spawner.spawn_free,
                        )
                        self.delta = 0
                        spawner.current += 1
