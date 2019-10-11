from dataclasses import dataclass
from planar import Point
from esper import Processor
import pygame 
from . import env
from .animation import AnimationComponent
from .datacl import Facing
from .datacl import GameObject
from .datacl import PlatformComponent
from .datacl import WallComponent
from .gfx import SpriteComponent
from .mechanics import LadderComponent
from .teleporter import TriggerComponent
from .teleporter import TeleporterState
from .movement import MotionComponent
from .movement import StopWatchComponent
from .movement import BallisticMotionComponent
from .movement import LinearMotionMarker
from .item import ItemState
from .item import PickupComponent
from .particles import ParticleEffect, ParticleGeneratorComponent
import random
from .inventory import InventoryComponent


class GoalComponent:
    pass


class DerplingGoalMarker:
    pass


class VictoryMarker:
    pass


class GoalTrampolineMarker:
    pass


class GoalTrampolineProcessor(Processor):
    def process(self, scene, delta):
        goals = self.world.get_components(GameObject, GoalTrampolineMarker)
        derplings = self.world.get_components(GameObject, VictoryMarker)
        for _, (goal, _) in goals:
            for derpling_id, (derpling, _) in derplings:
                if derpling.rect.colliderect(goal.rect):
                    derpling_anim = self.world.component_for_entity(
                        derpling_id, AnimationComponent
                    )
                    derpling_motion = self.world.component_for_entity(
                        derpling_id, MotionComponent
                    )

                    if self.world.has_component(derpling_id, WalkingDerplingMarker):
                        self.world.remove_component(derpling_id, WalkingDerplingMarker)
                        self.world.remove_component(derpling_id, LinearMotionMarker)
                        self.world.add_component(
                            derpling_id, BallisticMotionComponent()
                        )
                        self.world.add_component(derpling_id, StopWatchComponent())
                        derpling_anim.change_animation("fall")

                        angle_rand = random.randint(-10, 11)
                        angle_mag = random.randint(-400, 400)
                        derpling_motion.angle = 60 + angle_rand
                        derpling_motion.magnitude = 1600 + angle_mag


class GoalProcessor(Processor):
    def __init__(self):
        self.eid = None
        self.active = False

    def process(self, scene, delta):
        derplings_in_goal = self.world.get_component(DerplingGoalMarker)
        count_comp = next(iter(self.world.get_component(DerplingCountComponent)))

        for derpling_id, derpling in derplings_in_goal:
            derpling_anim = self.world.component_for_entity(
                derpling_id, AnimationComponent
            )
            derpling_motion = self.world.component_for_entity(
                derpling_id, MotionComponent
            )
            derpling_anim.change_animation("fall")

            self.world.remove_component(derpling_id, WalkingDerplingMarker)
            self.world.remove_component(derpling_id, DerplingGoalMarker)
            self.world.remove_component(derpling_id, LinearMotionMarker)
            self.world.add_component(derpling_id, BallisticMotionComponent())
            self.world.add_component(derpling_id, VictoryMarker())
            self.world.add_component(derpling_id, StopWatchComponent())

            derpling_motion.angle = 87.7
            derpling_motion.magnitude = 2000

            self.eid = derpling_id

        derplings_in_victory = self.world.get_component(VictoryMarker)
        if (
            len(derplings_in_victory) > 0
            and len(derplings_in_victory) == count_comp[1].derpling_count
        ):
            scene.hud_group = pygame.sprite.Group()
            if not self.active:
                goals = self.world.get_components(SpriteComponent, GoalTrampolineMarker)
                for _, (sprite, goal) in goals:
                    sprite.sprite.add(scene.sprite_group)

                cam_derpling = self.world.component_for_entity(self.eid, GameObject)
                cam_object = self.world.component_for_entity(scene.camera, GameObject)
                new_pos = Point(cam_derpling.rect.left, cam_derpling.rect.top - 8)

                cam_object.pos = new_pos
                scene.sprite_group.center(cam_object.pos)

                if self.world.has_component(self.eid, WalkingDerplingMarker):
                    scene.game_end = True
                    self.active = True


class DescendingDerplingMarker:
    pass


class ExplodingDerplingMarker:
    pass


class WalkingDerplingMarker:
    pass


class LadderDerplingMarker:
    pass


class GrownDerplingMarker:
    pass


class ShrinkDerplingMarker:
    pass


@dataclass
class DerplingCountComponent:
    derpling_count: int = 0


class DerplingCountProcessor(Processor):
    def process(self, scene, delta):
        derpling_count = len(
            [
                _
                for (_, d) in self.world.get_component(DerplingState)
                if not d.data["imprisoned"]
            ]
        )
        for _, count_component in self.world.get_component(DerplingCountComponent):
            count_component.derpling_count = derpling_count


class DerplingState:
    def __init__(self):
        self.data = {
            "last_collided_platform": None,
            "on_ladder_id": 0,
            "last_facing_direction": 90,
            "imprisoned": True,
        }
        self.dead = False
        self.fall_factor = 1.0


def ws_to_ss(pos: Point, scene):
    ss_pos = Point(
        pos.x - scene.map_layer.view_rect.x, pos.y - scene.map_layer.view_rect.y
    )
    return ss_pos


class DescendingDerplingProcessor(Processor):
    def process(self, scene, delta):
        """Check to see if we are in a platform, then snap to top of platform, then add walking marker class"""
        derplings = list(
            self.world.get_components(
                DescendingDerplingMarker,
                DerplingState,
                SpriteComponent,
                GameObject,
                StopWatchComponent,
                MotionComponent,
                AnimationComponent,
            )
        )
        platforms = list(self.world.get_components(PlatformComponent, GameObject))

        for (
            derpling_id,
            (
                _,
                derpling_state,
                derpling_sprite,
                derpling_object,
                stopwatch,
                derpling_motion,
                derpling_anim,
            ),
        ) in derplings:
            for platform_id, (_, platform_object) in platforms:
                derpling_rect = derpling_object.rect
                platform_rect = platform_object.rect

                if derpling_rect.colliderect(platform_rect):
                    self.world.remove_component(derpling_id, DescendingDerplingMarker)
                    self.world.remove_component(derpling_id, StopWatchComponent)

                    if (
                        stopwatch.elapsed_ms >= env.DEATH_FALL_TIME
                        and not derpling_state.data.get("has-umbrella", False)
                        and not self.world.has_component(derpling_id, VictoryMarker)
                    ):
                        derpling_anim.change_animation("death")
                        self.world.remove_component(derpling_id, MotionComponent)
                        self.world.add_component(derpling_id, ExplodingDerplingMarker())
                        explode_pos = Point(
                            (derpling_object.pos.x + derpling_object.w / 2),
                            derpling_object.pos.y + derpling_object.h,
                        )
                        self.world.create_entity(
                            ParticleGeneratorComponent.create_effect(
                                explode_pos, ParticleEffect.SMALL_EXPLOSION
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
                    else:
                        self.world.add_component(derpling_id, WalkingDerplingMarker())
                        y = platform_rect.top - derpling_rect.height
                        x = derpling_rect.left
                        derpling_anim.change_animation("walk")
                        derpling_state.data["has-umbrella"] = False
                        derpling_object.pos = Point(x, y)
                        derpling_state.data["attached-platform"] = platform_id
                        derpling_motion.angle = derpling_object.facing.value
                        derpling_motion.magnitude = env.WALK_SPEED


class ExplodingDerplingProcessor(Processor):
    def process(self, scene, delta):
        derplings = self.world.get_components(
            ExplodingDerplingMarker, AnimationComponent, SpriteComponent
        )
        for derpling_id, (_, animation_component, sprite) in derplings:
            if not animation_component.anim_set == "death":
                animation_component.change_animation("death")
            elif animation_component.stop:
                self.world.delete_entity(derpling_id)
                sprite.sprite.kill()


class AscendingLadderDerplingProcessor(Processor):
    def process(self, scene, delta):
        derplings = self.world.get_components(
            LadderDerplingMarker,
            SpriteComponent,
            DerplingState,
            MotionComponent,
            GameObject,
        )

        for (
            derpling_id,
            (_, derpling_sprite, derpling_state, derpling_motion, derpling_object),
        ) in derplings:
            ladder_id = derpling_state.data["attached-ladder"]
            ladder_object = self.world.component_for_entity(ladder_id, GameObject)
            if not derpling_object.rect.colliderect(ladder_object.rect):
                for lid, (gobj, lobj) in self.world.get_components(
                    GameObject, LadderComponent
                ):
                    if derpling_object.rect.colliderect(gobj.rect):
                        if gobj.rect.top == ladder_object.rect.top - env.GRID_SIZE:
                            derpling_state.data["attached-ladder"] = lid

                if derpling_state.data["attached-ladder"] == ladder_id:
                    derpling_object.pos = Point(
                        derpling_object.pos.x, derpling_object.pos.y - 10
                    )
                    self.world.remove_component(derpling_id, LadderDerplingMarker)
                    self.world.add_component(derpling_id, StopWatchComponent())
                    self.world.add_component(derpling_id, DescendingDerplingMarker())
                    derpling_motion.angle = 90
                    derpling_motion.magnitude = env.FALL_SPEED
                    derpling_state.data["attached-ladder"] = None
            

class WalkingDerplingProcessor(Processor):
    def process(self, scene, delta):
        for derpling_id, _ in self.world.get_component(WalkingDerplingMarker):
            self.handle_pickup(derpling_id)
            if self.handle_walking_off(derpling_id):
                continue
            self.check_collides_with_wall(derpling_id)
            self.check_collides_with_ladder(derpling_id)
            self.check_collides_with_trigger(derpling_id)
            self.check_collides_with_teleporter(derpling_id)
            self.check_collides_with_item(derpling_id, scene)
            self.check_collides_with_goal(derpling_id, scene)

    def check_collides_with_goal(self, derpling_id, scene):
        goal = self.world.component_for_entity(scene.goal_id, GameObject)
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)

        if derpling_object.rect.colliderect(goal.rect):
            if not self.world.has_component(derpling_id, DerplingGoalMarker):
                self.world.add_component(derpling_id, DerplingGoalMarker())

    def handle_pickup(self, derpling_id):
        pickups = self.world.get_components(
            PickupComponent, GameObject, SpriteComponent
        )
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        for pickup_id, (pickup, pickup_object, pickup_sprite) in pickups:
            if pickup_object.rect.colliderect(derpling_object.rect):
                inventory = self.world.get_component(InventoryComponent)
                for _, inv in inventory:
                    pickup_sprite.sprite.kill()
                    self.world.delete_entity(pickup_id)
                    setattr(inv, pickup.item_type, pickup.amount)

    def handle_walking_off(self, derpling_id):
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        derpling_state = self.world.component_for_entity(derpling_id, DerplingState)
        derpling_motion = self.world.component_for_entity(derpling_id, MotionComponent)
        derpling_animation = self.world.component_for_entity(
            derpling_id, AnimationComponent
        )

        platform_rect = self.world.component_for_entity(
            derpling_state.data["attached-platform"], GameObject
        ).rect
        if (
            derpling_object.rect.left > platform_rect.right
            or derpling_object.rect.right < platform_rect.left
        ) and not self.world.has_component(derpling_id, GrownDerplingMarker):
            self.world.add_component(derpling_id, DescendingDerplingMarker())
            self.world.add_component(derpling_id, StopWatchComponent())
            self.world.remove_component(derpling_id, WalkingDerplingMarker)
            derpling_animation.change_animation("fall")
            derpling_motion.angle = 90
            if derpling_state.data.get("has-umbrella", False):
                derpling_motion.magnitude = env.UMBRELLA_SPEED
            else:
                derpling_motion.magnitude = env.FALL_SPEED
            return True
        return False

    def check_collides_with_wall(self, derpling_id):
        walls = self.world.get_components(WallComponent, GameObject)
        for _, (_, wall_object) in walls:
            self.handle_wall_collision(derpling_id, wall_object)

    def handle_wall_collision(self, derpling_id, other_object):
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        derpling_motion = self.world.component_for_entity(derpling_id, MotionComponent)
        derpling_animation = self.world.component_for_entity(
            derpling_id, AnimationComponent
        )

        if other_object.rect.colliderect(derpling_object.rect):
            if derpling_object.facing == Facing.RIGHT:
                derpling_object.pos = Point(
                    other_object.rect.left - derpling_object.rect.width,
                    derpling_object.rect.y,
                )
                derpling_object.facing = Facing.LEFT
            else:
                derpling_object.pos = Point(
                    other_object.rect.right, derpling_object.rect.y
                )
                derpling_object.facing = Facing.RIGHT
            derpling_motion.angle = derpling_object.facing.value
            derpling_animation.mirror = not derpling_animation.mirror

    def check_collides_with_ladder(self, derpling_id):
        ladders = self.world.get_components(
            LadderComponent, GameObject, LadderComponent
        )
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        for ladder_id, (_, ladder_object, ladder_comp) in ladders:
            if derpling_object.rect.colliderect(ladder_object.rect):
                if self.world.has_component(derpling_id, WalkingDerplingMarker):
                    self.world.remove_component(derpling_id, WalkingDerplingMarker)
                    self.world.add_component(derpling_id, LadderDerplingMarker())
                motion = self.world.component_for_entity(derpling_id, MotionComponent)
                motion.angle = 270
                motion.magnitude = env.WALK_SPEED
                derpling_object.pos = Point(
                    ladder_object.rect.left, derpling_object.pos.y
                )
                derpling_state = self.world.component_for_entity(
                    derpling_id, DerplingState
                )

                derpling_state.data["attached-ladder"] = ladder_id
                ladder_comp.in_use = True
                self.world.component_for_entity(
                    derpling_id, AnimationComponent
                ).change_animation("climb")
                return

    def check_collides_with_trigger(self, derpling_id):
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        triggers = self.world.get_components(GameObject, TriggerComponent)
        for _, (trigger_object, trigger) in triggers:
            if derpling_object.rect.colliderect(trigger_object.rect):
                trigger.active = True

    def check_collides_with_teleporter(self, derpling_id):
        teleporters = self.world.get_components(GameObject, TeleporterState)
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        derpling_state = self.world.component_for_entity(derpling_id, DerplingState)
        for _, (tp_object, teleporter) in teleporters:
            if (
                tp_object.rect.colliderect(derpling_object.rect)
                and teleporter.is_open()
                and derpling_state.data["imprisoned"]
            ):
                game_object = self.world.component_for_entity(derpling_id, GameObject)

                other_tp_rect = self.world.component_for_entity(
                    teleporter.counter_part_eid, SpriteComponent
                ).sprite.rect
                other_tp = self.world.component_for_entity(
                    teleporter.counter_part_eid, TeleporterState
                )
                teleporter.count += 1
                other_tp.count += 1

                # side = 0 (left), side = 1 (right)
                if other_tp.properties["side"]:
                    game_object.pos = Point(other_tp_rect.right, other_tp_rect.top)
                else:
                    game_object.pos = Point(
                        other_tp_rect.left - derpling_object.rect.width,
                        other_tp_rect.top,
                    )
                # if we get in and out on the same side we need to change walking direction
                if other_tp.properties["side"] == teleporter.properties["side"]:
                    motion = self.world.component_for_entity(
                        derpling_id, MotionComponent
                    )
                    motion.angle = (motion.angle + 180) % 360
                    game_object.facing = (
                        Facing.LEFT
                        if game_object.facing == Facing.RIGHT
                        else Facing.LEFT
                    )
                    anim = self.world.component_for_entity(
                        derpling_id, AnimationComponent
                    )
                    anim.mirror = not anim.mirror

                derpling_state.data["imprisoned"] = False
                derpling_object.rect.topleft = (game_object.pos.x, game_object.pos.y)
                self.world.remove_component(derpling_id, WalkingDerplingMarker)
                self.world.add_component(derpling_id, DescendingDerplingMarker())
                self.world.add_component(derpling_id, StopWatchComponent())
                #  TODO: I wonder if we should change the animation or "fake fall" so we fall in gameplay terms, but the player doesn't see it
                self.world.component_for_entity(
                    derpling_id, AnimationComponent
                ).change_animation("fall")
                self.world.component_for_entity(derpling_id, MotionComponent).angle = 90

    def check_collides_with_item(self, derpling_id, scene):
        items = self.world.get_components(GameObject, ItemState)
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        derpling_state = self.world.component_for_entity(derpling_id, DerplingState)

        for item_id, (item_object, item_state) in items:
            if item_state.is_active() and item_object.rect.colliderect(
                derpling_object.rect
            ):
                if item_state.type == "umbrella":
                    derpling_state.data["has-umbrella"] = True
                if item_state.type == "stop_sign":
                    self.handle_wall_collision(derpling_id, item_object)
                if item_state.type == "trampoline" or item_state.type == "jetpack":
                    self.handle_trampoline_and_jetpack(scene, derpling_id, item_state)
                if item_state.type == "inflator" or item_state.type == "deflator":
                    self.handle_growth(derpling_id, item_id, item_state.type, scene)

    def handle_trampoline_and_jetpack(self, scene, derpling_id, item):
        derpling_anim = self.world.component_for_entity(derpling_id, AnimationComponent)
        derpling_motion = self.world.component_for_entity(derpling_id, MotionComponent)

        self.world.remove_component(derpling_id, WalkingDerplingMarker)
        self.world.remove_component(derpling_id, LinearMotionMarker)
        self.world.add_component(
            derpling_id, BallisticMotionComponent(is_jetpack=(item.type == "jetpack"))
        )
        self.world.add_component(derpling_id, StopWatchComponent())
        derpling_anim.change_animation("fall")

        derpling_motion.angle = 60 if item.type == "trampoline" else 85
        derpling_motion.magnitude = 1600 if item.type == "trampoline" else 3000
        if item.type == "jetpack":
            scene.sounds["sounds"]["wind"].set_volume(0.3)
            scene.sounds["sounds"]["wind"].play(loops=0, maxtime=0, fade_ms=0)

            derpling_object = self.world.component_for_entity(derpling_id, GameObject)

            self.world.create_entity(
                ParticleGeneratorComponent.create_effect(
                    derpling_object.pos, ParticleEffect.SMOKE
                )
            )
        else:
            scene.sounds["sounds"]["boing"].play(loops=0, maxtime=0, fade_ms=0)

    def handle_growth(self, derpling_id, item_id, item_type, scene):
        derpling_object = self.world.component_for_entity(derpling_id, GameObject)
        derpling_anim = self.world.component_for_entity(derpling_id, AnimationComponent)
        derpling_state = self.world.component_for_entity(derpling_id, DerplingState)
        derpling_object.rect.w = env.LEM_WIDTH * (2 if item_type == "inflator" else 0.5)
        derpling_object.rect.h = env.LEM_HEIGHT * (
            2 if item_type == "inflator" else 0.5
        )
        platform = self.world.component_for_entity(
            derpling_state.data["attached-platform"], GameObject
        )
        self.world.add_component(derpling_id, StopWatchComponent())
        self.world.add_component(derpling_id, GrownDerplingMarker() if item_type == "inflator" else ShrinkDerplingMarker())
        derpling_object.pos = Point(
            derpling_object.rect.left, platform.rect.top - derpling_object.rect.height
        )

        if item_type == "deflator":
            scene.sounds["sounds"]["deflate"].play(loops=0, maxtime=0, fade_ms=0)
        else:
            scene.sounds["sounds"]["inflate"].play(loops=0, maxtime=0, fade_ms=0)

        sprite = self.world.component_for_entity(item_id, SpriteComponent)
        sprite.sprite.kill()
        self.world.delete_entity(item_id)

        derpling_anim.change_animation(item_type)


class BallisticDerplingProcessor(Processor):
    def process(self, scene, delta):
        derplings = list(
            self.world.get_components(
                BallisticMotionComponent,
                DerplingState,
                SpriteComponent,
                GameObject,
                MotionComponent,
                AnimationComponent,
            )
        )
        platforms = list(self.world.get_components(PlatformComponent, GameObject))
        walls = list(self.world.get_components(WallComponent, GameObject))
        for (
            derpling_id,
            (
                _,
                derpling_state,
                derpling_sprite,
                derpling_object,
                derpling_motion,
                derpling_anim,
            ),
        ) in derplings:
            for wall_id, (_, wall_object) in walls:
                derpling_object = self.world.component_for_entity(
                    derpling_id, GameObject
                )
                derpling_motion = self.world.component_for_entity(
                    derpling_id, MotionComponent
                )

                if wall_object.rect.colliderect(derpling_object.rect):
                    self.world.remove_component(derpling_id, BallisticMotionComponent)
                    self.world.add_component(derpling_id, LinearMotionMarker())
                    derpling_rect = derpling_object.rect
                    self.world.add_component(derpling_id, DescendingDerplingMarker())
                    self.world.add_component(derpling_id, StopWatchComponent())
                    y = derpling_rect.top
                    if derpling_rect.centerx < wall_object.rect.centerx:
                        x = wall_object.rect.left - derpling_rect.width
                    else:
                        x = wall_object.rect.right
                    derpling_object.pos = Point(x, y)
                    derpling_motion.angle = 90
                    derpling_motion.magnitude = env.FALL_SPEED

        for (
            derpling_id,
            (
                _,
                derpling_state,
                derpling_sprite,
                derpling_object,
                derpling_motion,
                derpling_anim,
            ),
        ) in derplings:
            for platform_id, (_, platform_object) in platforms:
                derpling_rect = derpling_object.rect
                platform_rect = platform_object.rect

                if derpling_rect.colliderect(platform_rect):
                    if self.world.has_component(derpling_id, BallisticMotionComponent):
                        self.world.remove_component(
                            derpling_id, BallisticMotionComponent
                        )
                    self.world.add_component(derpling_id, LinearMotionMarker())
                    if platform_rect.centery < derpling_rect.centery:
                        self.world.add_component(
                            derpling_id, DescendingDerplingMarker()
                        )
                        self.world.add_component(derpling_id, StopWatchComponent())
                        y = platform_rect.bottom
                        x = derpling_rect.left
                        derpling_object.pos = Point(x, y)
                        derpling_motion.angle = 90
                        derpling_motion.magnitude = env.FALL_SPEED
                    else:
                        self.world.add_component(derpling_id, WalkingDerplingMarker())
                        y = platform_rect.top - derpling_rect.height
                        x = derpling_rect.left
                        derpling_anim.change_animation("walk")
                        derpling_object.pos = Point(x, y)
                        derpling_state.data["attached-platform"] = platform_id
                        derpling_motion.angle = derpling_object.facing.value
                        derpling_motion.magnitude = env.WALK_SPEED


class DerplingGrownProcessor(Processor):
    def process(self, scene, delta):
        derplings = self.world.get_components(
            GrownDerplingMarker,
            DerplingState,
            GameObject,
            StopWatchComponent,
            AnimationComponent,
        )
        derplings += self.world.get_components(
            ShrinkDerplingMarker,
            DerplingState,
            GameObject,
            StopWatchComponent,
            AnimationComponent,
        )
        
        for (
            derpling_id,
            (_, derpling_state, derpling_object, stopwatch, derpling_anim),
        ) in derplings:
            platform_id = derpling_state.data["attached-platform"]
            platform_rect = self.world.component_for_entity(
                platform_id, GameObject
            ).rect
            if self.world.has_component(derpling_id, ShrinkDerplingMarker):
                if (
                    derpling_object.rect.left > platform_rect.right
                    or derpling_object.rect.right < platform_rect.left
                ):
                    self.world.remove_component(derpling_id, ShrinkDerplingMarker)
                    derpling_object.rect.w = env.LEM_WIDTH
                    derpling_object.rect.h = env.LEM_HEIGHT
                    pos = (derpling_object.rect.left, platform_rect.top - env.LEM_HEIGHT)
                    derpling_object.pos = pos
                    self.world.remove_component(derpling_id, StopWatchComponent)

            if stopwatch.elapsed_ms >= 5000:
                check_rect = pygame.Rect(
                    derpling_object.rect.left - 8,
                    derpling_object.rect.top - 8,
                    env.GRID_SIZE // 2,
                    env.GRID_SIZE // 2
                )
                platforms = self.world.get_components(GameObject, PlatformComponent)
                for _, (platform_object, platform_comp) in platforms:
                    if platform_object.rect.colliderect(check_rect) and self.world.has_component(derpling_id, ShrinkDerplingMarker):
                        return

                self.world.remove_component(derpling_id, StopWatchComponent)
                if self.world.has_component(derpling_id, GrownDerplingMarker):
                    self.world.remove_component(derpling_id, GrownDerplingMarker)
                    scene.sounds["sounds"]["inflate"].play(
                        loops=0, maxtime=0, fade_ms=0
                    )
                elif self.world.has_component(derpling_id, ShrinkDerplingMarker):
                    scene.sounds["sounds"]["deflate"].play(
                        loops=0, maxtime=0, fade_ms=0
                    )
                    self.world.remove_component(derpling_id, ShrinkDerplingMarker)
                pos = Point(derpling_object.rect.left, platform_rect.top - env.LEM_HEIGHT)
                derpling_object.rect.w = env.LEM_WIDTH
                derpling_object.rect.h = env.LEM_HEIGHT
                derpling_object.pos = pos
                derpling_anim.change_animation("walk")


class DebugProcessor(Processor):
    def process(self, scene, delta):
        for eid, _ in self.world.get_component(DerplingState):
            components = self.world.components_for_entity(eid)
            classes = [
                c.__class__.__name__
                for c in components
                if "marker" in c.__class__.__name__.lower()
            ]
            s = " - ".join(sorted(classes))
            print(s)
            pygame.display.set_caption(s)
