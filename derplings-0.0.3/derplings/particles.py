from enum import Enum, auto
from random import randint, choice, uniform
from typing import List, Callable
from dataclasses import dataclass, field
from itertools import count
from collections import OrderedDict
import easing_functions

from esper import Processor, World
from planar import Point, Vec2

from zkit.scenes import Scene

import pygame
from pygame.draw import circle
from pygame.color import Color
from pygame.display import flip

from . import env


class ParticleEffect(Enum):
    DEFAULT = auto()
    SMALL_EXPLOSION = auto()
    MEDIUM_EXPLOSION = auto()
    LARGE_EXPLOSION = auto()
    SMOKE = auto()
    CONFETTI = auto()


class ParticleGeneratorComponent:
    pass


@dataclass
class ParticleGeneratorComponent:
    origin: Point
    colors: List[str] = field(default_factory=lambda: ["lightblue", "blue"])
    min_particle_size: int = 1
    max_particle_size: int = 3
    alpha_start: int = 0
    alpha_end: int = 255
    alpha_easing_fn: Callable = easing_functions.CubicEaseOut
    min_magnitude: float = 10.0  # pixels/second
    max_magnitude: float = 1000.0  # pixels/second
    num_particles: int = 100
    min_duration: int = 100  # MS
    max_duration: int = 300  # MS
    min_angle: float = 0.0
    max_angle: float = 359.0
    particles_emitted: int = 0
    emit_frequency: int = 100  # MS
    time_since_emit: int = 0  # MS
    particles_per_emit: int = -1  # set to -1 to blast out all particles in one frame

    @staticmethod
    def create_effect(pos: Point, effect: ParticleEffect) -> ParticleGeneratorComponent:
        return {
            ParticleEffect.DEFAULT: ParticleGeneratorComponent(pos),
            ParticleEffect.SMALL_EXPLOSION: ParticleGeneratorComponent(
                pos,
                colors=["red", "orangered4", "yellow", "orange", "white"],
                min_particle_size=1,
                max_particle_size=3,
                min_magnitude=800,
                max_magnitude=2000,
                emit_frequency=100,
                particles_per_emit=-1,
                min_duration=50,
                max_duration=250,
                num_particles=500,
            ),
            ParticleEffect.MEDIUM_EXPLOSION: ParticleGeneratorComponent(
                pos,
                colors=["red", "orangered4", "yellow", "orange", "white"],
                min_particle_size=1,
                max_particle_size=4,
                min_magnitude=300,
                max_magnitude=400,
                emit_frequency=100,
                particles_per_emit=100,
                min_duration=150,
                max_duration=250,
                num_particles=200,
            ),
            ParticleEffect.LARGE_EXPLOSION: ParticleGeneratorComponent(
                pos,
                colors=["red", "orangered4", "yellow", "orange", "white"],
                min_particle_size=2,
                max_particle_size=5,
                min_magnitude=300,
                max_magnitude=400,
                emit_frequency=100,
                particles_per_emit=100,
                min_duration=250,
                max_duration=500,
                num_particles=400,
            ),
            ParticleEffect.SMOKE: ParticleGeneratorComponent(
                pos,
                colors=["white", "grey", "darkgrey", "lightgrey"],
                alpha_easing_fn=easing_functions.SineEaseOut,
                alpha_start=128,
                alpha_end=0,
                min_particle_size=3,
                max_particle_size=10,
                min_magnitude=10.0,
                max_magnitude=50.0,
                min_duration=500,
                max_duration=1000,
                min_angle=220,
                max_angle=320,
                num_particles=3
            ),
            ParticleEffect.CONFETTI: ParticleGeneratorComponent(
                pos,
                colors=["red", "white", "blue", "orange", "purple", "green"],
                alpha_easing_fn=easing_functions.BounceEaseInOut,
                alpha_start=100,
                alpha_end=255,
                max_duration=1000,
                min_angle=45,
                max_angle=135,
            ),
        }[effect]


@dataclass
class Particle:
    pos: Point
    angle: float = 90
    magnitude: float = 1.0
    lifetime: int = 250
    time_remaining: int = 250
    color: str = "white"
    alpha: int = 255
    size: int = 3
    alpha_start: int = 0
    alpha_end: int = 255
    alpha_easing_fn: Callable = None


class ParticleProcessor(Processor):
    def __init__(self):
        self.particles = list()

    def process(self, scene, delta):
        for generator_id, generator in self.world.get_component(
            ParticleGeneratorComponent
        ):
            generator.time_since_emit += delta
            emit = generator.time_since_emit >= generator.emit_frequency
            if emit and generator.particles_emitted < generator.num_particles:
                generator.time_since_emit = 0
                particles_per_emit = (
                    generator.num_particles
                    if generator.particles_per_emit == -1
                    else generator.particles_per_emit
                )
                for i in range(particles_per_emit):
                    particle = Particle(generator.origin)
                    particle.angle = uniform(generator.min_angle, generator.max_angle)
                    particle.color = choice(generator.colors)
                    particle.size = randint(
                        generator.min_particle_size, generator.max_particle_size
                    )
                    particle.magnitude = uniform(
                        generator.min_magnitude, generator.max_magnitude
                    )
                    particle.lifetime = generator.time_remaining = randint(
                        generator.min_duration, generator.max_duration
                    )
                    particle.time_remaining = particle.lifetime
                    particle.alpha_start = generator.alpha_start
                    particle.alpha_end = generator.alpha_end
                    particle.alpha_easing_fn = generator.alpha_easing_fn(
                        start=particle.alpha_start,
                        end=particle.alpha_end,
                        duration=particle.lifetime,
                    )
                    self.particles.append(particle)
                    generator.particles_emitted += 1
            if generator.particles_emitted >= generator.num_particles:
                self.world.delete_entity(generator_id)
        self.update_particles(scene, delta)

    def update_particles(self, scene, delta):
        live_particles = list()
        integration = (scene.game.target_fps / 1000.0) * delta
        for particle in self.particles:
            particle.time_remaining -= delta
            if particle.time_remaining > 0:
                live_particles.append(particle)
                particle.pos += Vec2.polar(
                    particle.angle,
                    particle.magnitude * integration / scene.game.target_fps,
                )
                particle.alpha = particle.alpha_easing_fn.ease(particle.time_remaining)
        self.particles = live_particles


class ParticleTestScene(Scene):

    CIRCLE_CACHE = dict()

    def __init__(self):
        super(ParticleTestScene, self).__init__("particle-test")
        self.processor = None
        self.world = None
        self.selected_effect = ParticleEffect.DEFAULT
        self.effect_map = OrderedDict()
        for i, e in zip(count(0, 1), ParticleEffect):
            self.effect_map[str(i)] = e

    def setup(self):
        self.processor = ParticleProcessor()
        self.world = World()
        self.world.add_processor(self.processor)
        self.world.create_entity(
            ParticleGeneratorComponent(Point(env.SCR_WIDTH / 2, env.SCR_HEIGHT / 2))
        )

    def teardown(self):
        pass

    def resume(self):
        pass

    def draw(self, surface):
        for particle in self.processor.particles:
            color = Color(particle.color)
            color.a = max(0, min(255, abs(int(particle.alpha))))
            surf_key = (particle.size, particle.color, color.a)
            surf = self.CIRCLE_CACHE.get(surf_key, None)
            if surf is None:
                size = particle.size * 2
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                circle(surf, color, (particle.size, particle.size), particle.size)
                self.CIRCLE_CACHE[surf_key] = surf
            surface.blit(surf, (int(particle.pos.x), int(particle.pos.y)))
        flip()

    def update(self, delta, events):
        self.world.process(self, delta)
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                self.world.create_entity(
                    ParticleGeneratorComponent.create_effect(
                        Point(*event.pos), self.selected_effect
                    )
                )
            elif event.type == pygame.KEYDOWN:
                self.selected_effect = self.effect_map.get(
                    event.unicode, ParticleEffect.DEFAULT
                )

    def clear(self, surface):
        surface.fill((0, 0, 0))
