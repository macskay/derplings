from esper import Processor
from planar import Vec2, Point

from .datacl import GameObject, Facing
import math
from dataclasses import dataclass
from .particles import ParticleGeneratorComponent, ParticleEffect


@dataclass
class StopWatchComponent:
    elapsed_ms: int = 0


class StopWatchProcessor(Processor):
    def process(self, scene, delta):
        for _, stop_watch in self.world.get_component(StopWatchComponent):
            stop_watch.elapsed_ms += delta


@dataclass
class MotionComponent:
    angle: float = 0
    magnitude: float = 0


class LinearMotionProcessor(Processor):
    def __init__(self):
        self.delta = 0

    def process(self, scene, delta):
        integration = (scene.game.target_fps / 1000.0) * delta

        for eid, (_, game_object, motion_comp) in self.world.get_components(
            LinearMotionMarker, GameObject, MotionComponent
        ):
            self.delta += delta
            motion = (
                Vec2.polar(motion_comp.angle, motion_comp.magnitude * integration)
                / scene.game.target_fps
            )
            game_object.pos += motion


@dataclass
class BallisticMotionComponent:
    start_pos: Point = None
    is_jetpack: bool = False
    time_to_travel: float = 0.0


class LinearMotionMarker:
    pass


class BallisticMotionProcessor(Processor):
    def process(self, scene, delta):
        delta = 17
        integration = (scene.game.target_fps / 1000.0) * delta

        for (
            _,
            (ballistic_object, game_object, motion_comp, stopwatch),
        ) in self.world.get_components(
            BallisticMotionComponent, GameObject, MotionComponent, StopWatchComponent
        ):
            v0 = (13 * motion_comp.magnitude * integration) / scene.game.target_fps
            g = 9.81 * 30
            t = stopwatch.elapsed_ms / 1000.0
            beta = math.radians(motion_comp.angle)

            if ballistic_object.start_pos is None:
                ballistic_object.start_pos = game_object.pos
                ballistic_object.time_to_travel = ((2 * v0 * math.sin(beta)) / g) * 1000

            x = v0 * t * math.cos(beta)
            y = (v0 * t * math.sin(beta)) - (0.5 * g * t ** 2)
            if game_object.facing == Facing.LEFT:
                x *= -1
            motion = Vec2(x, y * (-1))
            game_object.pos = ballistic_object.start_pos + motion

            if ballistic_object.is_jetpack:
                if game_object.pos.distance_to(ballistic_object.start_pos) % 5 < 4:
                    if (
                        stopwatch.elapsed_ms
                        < (ballistic_object.time_to_travel / 2) - 1000
                    ):
                        self.world.create_entity(
                            ParticleGeneratorComponent.create_effect(
                                game_object.pos, ParticleEffect.SMOKE
                            )
                        )
