from itertools import product

import pygame
import pygame.transform
import pygame.image
from pygame.draw import circle
from pygame.color import Color
from pygame.sprite import LayeredUpdates
import pyscroll
from esper import World
from planar import Point
from pygame.sprite import Sprite, Rect
from pygame.surface import Surface
import os
import pytmx

from .autotiler import AutoTiler
from zkit.scenes import Scene

from . import env
from .animation import AnimationProcessor, AnimationComponent
from .camera import CameraProcessor, CameraComponent
from .datacl import Facing
from .datacl import GameObject, PlatformComponent, WallComponent, WeakPlatformMarker
from .derpling import AscendingLadderDerplingProcessor
from .derpling import BallisticDerplingProcessor
from .derpling import DerplingCountProcessor
from .derpling import DerplingGrownProcessor
from .derpling import DerplingState
from .derpling import DescendingDerplingMarker
from .derpling import DescendingDerplingProcessor
from .derpling import ExplodingDerplingProcessor
from .derpling import GoalComponent
from .derpling import GoalProcessor
from .derpling import GoalTrampolineMarker
from .derpling import GoalTrampolineProcessor
from .derpling import WalkingDerplingProcessor
from .derpling import LadderDerplingMarker
from .hud import HUDBuilder
from .hud import InventoryComponent
from .hud import LABEL_DATA
from .hud import LabelBindingProcessor
from .hud import LabelProcessor
from .mechanics import TNTProcessor, TNTComponent, BlastProcessor
from .particles import ParticleGeneratorComponent
from .particles import ParticleProcessor

# from .derpling import DebugProcessor
from .gfx import SpriteProcessor, SpriteComponent, GraphicsLoader
from .item import ItemProcessor, ItemState, PickupComponent
from .mechanics import LadderComponent
from .movement import (
    LinearMotionProcessor,
    BallisticMotionProcessor,
    StopWatchProcessor,
    MotionComponent,
    StopWatchComponent,
    LinearMotionMarker,
)
from .sfx import SoundComponent, SoundLoader
from .spawn import SpawnProcessor, SpawnComponent
from .teleporter import TeleporterState, TriggerComponent, TeleporterProcessor


class NoItemZoneMarker:
    pass


class TowerScene(Scene):
    CIRCLE_CACHE = dict()
    SCREEN_RECT = Rect(0, 0, env.SCR_WIDTH, env.SCR_HEIGHT)

    def __init__(self, args):
        super(TowerScene, self).__init__("tower")
        self.world = None
        self.args = args
        # calm pycharm down
        self.assets = None
        self.tiled_data = None
        self.map_layer = None
        self.sprite_group = None
        self.grid = None
        self.camera = None
        self.item_selected = None
        self.item_inventory_id = None
        self.no_derplings = 0
        self.hud_group = LayeredUpdates()
        self.item_group = LayeredUpdates()
        self.derpling_group = LayeredUpdates()
        self.ladder_start_segment = None
        self.goal_id = None
        self.game_end = False

    def setup(self):
        self.world = World()
        processors = [
            GoalProcessor(),
            CameraProcessor(),
            LinearMotionProcessor(),
            BallisticMotionProcessor(),
            SpawnProcessor(),
            DerplingCountProcessor(),
            AscendingLadderDerplingProcessor(),
            DescendingDerplingProcessor(),
            DerplingGrownProcessor(),
            WalkingDerplingProcessor(),
            ExplodingDerplingProcessor(),
            BlastProcessor(),
            BallisticDerplingProcessor(),
            GoalTrampolineProcessor(),
            AnimationProcessor(),
            StopWatchProcessor(),
            TeleporterProcessor(),
            ItemProcessor(),
            TNTProcessor(),
            LabelBindingProcessor(),
            LabelProcessor(),
            SpriteProcessor(),
            ParticleProcessor(),
            # DebugProcessor(), Add me and set FPS to 1 to debug the derpling states
        ]

        for processor in processors:
            self.world.add_processor(processor)

        self.assets = GraphicsLoader()
        self.sounds = SoundLoader()
        self.tiled_data = pytmx.load_pygame(
            os.path.join("assets", "maps", self.args.map)
        )

        # self.tiled_data = pytmx.load_pygame(
        #     os.path.join("assets", "maps", "testmap.tmx")
        # )

        # use auto tiler
        if 0:
            empty = [list([0] * 1024) for i in range(1024)]
            map_data = AutoTiler(
                empty, (self.tiled_data.tilewidth, self.tiled_data.tileheight)
            )
            map_data.map_size = self.tiled_data.width, self.tiled_data.height
            self.map_layer = pyscroll.BufferedRenderer(
                map_data, (1344, 768), alpha=True
            )
            self.sprite_group = pyscroll.PyscrollGroup(map_layer=self.map_layer)
            self.load_map_objects()
            map_data.tile_class_map = self.gridify()
            self.map_layer.set_size((1344, 768))
        else:
            map_data = pyscroll.TiledMapData(self.tiled_data)  # for visuals only
            self.map_layer = pyscroll.BufferedRenderer(map_data, (1344, 768))
            self.sprite_group = pyscroll.PyscrollGroup(map_layer=self.map_layer)
            self.load_map_objects()

        self.camera = self.create_camera()
        self.create_hud()

    def load_map_objects(self):
        for layer in self.tiled_data.layers:
            for obj in layer:
                if layer.name == "Static":
                    is_wall = True if obj.type == "Wall" else False
                    if is_wall:
                        self.create_wall(Point(obj.x, obj.y), obj.width, obj.height)
                    else:
                        self.create_platform(
                            Point(obj.x, obj.y),
                            obj.width,
                            obj.height,
                            getattr(obj, "is_weak", False),
                        )
                elif layer.name == "Spawner":
                    self.create_spawner(
                        Point(obj.x, obj.y),
                        getattr(obj, "spawn_free", False),
                        obj.properties["amount"],
                    )
                elif layer.name == "Ladder":
                    self.create_ladder(Point(obj.x, obj.y), obj.height)
                elif layer.name == "GoalTrampoline":
                    self.create_goal_trampoline(Point(obj.x, obj.y), obj.height)
                elif layer.name == "Teleporter":
                    self.create_teleporter(
                        Point(obj.x, obj.y), obj.width, obj.height, obj.properties
                    )
                elif layer.name == "Trigger":
                    self.create_trigger(
                        Point(obj.x, obj.y),
                        obj.width,
                        obj.height,
                        obj.properties["trigger_id"],
                    )
                elif layer.name == "Item":
                    self.create_pickup(
                        Point(obj.x, obj.y), obj.width, obj.height, obj.properties
                    )
                elif layer.name == "Goal":
                    self.create_goal(Point(obj.x, obj.y), obj.width, obj.height)
                elif layer.name == "NoItemZone":
                    self.create_no_item_zone(Point(obj.x, obj.y), obj.width, obj.height)

    def gridify(self):
        """ scan the entire map and reduce it into tiles

        WIP.  not fast.

        :return:
        """
        map_data = self.tiled_data
        grid = list()
        for y in range(map_data.height):
            grid.append([1] * map_data.width)

        sensor = pygame.Rect(0, 0, map_data.tilewidth, map_data.tileheight)
        platforms = list(self.world.get_components(GameObject, PlatformComponent))
        for y, x in product(range(0, map_data.height), range(0, map_data.width)):
            sensor.x = x * map_data.tilewidth
            sensor.y = y * map_data.tileheight
            for eid, (game_object, plat_comp) in platforms:
                if sensor.colliderect(
                    (game_object.pos, (game_object.w, game_object.h))
                ):
                    grid[y][x] = 2
                    break

        return grid

    def teardown(self):
        self.world.clear_database()

    def resume(self):
        pass

    def draw(self, surface):
        self.sprite_group.draw(surface)
        self.item_group.draw(surface)
        self.draw_particles(surface)
        self.hud_group.draw(surface)
        pygame.display.flip()

    def draw_particles(self, surface):
        processor = self.world.get_processor(ParticleProcessor)
        for particle in processor.particles:
            screen_pos = Point(
                particle.pos.x - self.map_layer.view_rect.x,
                particle.pos.y - self.map_layer.view_rect.y,
            )

            if self.SCREEN_RECT.collidepoint(screen_pos):
                color = Color(particle.color)
                color.a = max(0, min(255, abs(int(particle.alpha))))
                surf_key = (particle.size, particle.color, color.a)
                surf = self.CIRCLE_CACHE.get(surf_key, None)
                if surf is None:
                    size = particle.size * 2
                    surf = pygame.Surface((size, size), pygame.SRCALPHA)
                    circle(surf, color, (particle.size, particle.size), particle.size)
                    self.CIRCLE_CACHE[surf_key] = surf
                surface.blit(surf, screen_pos)

    def update(self, delta, events):
        for event in events:
            # if self.args.debug:
            #     handle_debug_input(self, event)

            if event.type == pygame.KEYUP:
                self.handle_keyboard_input(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_input(event)

        self.sprite_group.update()
        self.hud_group.update()
        self.world.process(self, delta)

    def get_tile_coords(self, pos: Point):
        pos = Point(*pygame.mouse.get_pos())
        x = (pos.x + self.map_layer.view_rect.left) // 32 * 32
        y = (pos.y + self.map_layer.view_rect.top) // 32 * 32
        return Point(x, y)

    def clear(self, surface):
        pass  # pyscroll fills the background so pointless to clear here

    def create_sprite(
        self, pos: Point, w: int, h: int, layer: int = 0, icon_name: str = "placeholder"
    ):
        sprite = Sprite()
        self.sprite_group.add(sprite, layer=layer)
        sprite.rect = Rect(pos.x, pos.y, w, h)
        surf = Surface(sprite.rect.size)
        sprite.image = surf.convert_alpha()

        if icon_name == "invisible":
            sprite.image.fill((0, 0, 0, 0))
            return sprite
        if icon_name not in self.assets["icons"].keys():
            color = (255, 0, 0) if icon_name == "weak_platform" else (128, 128, 128)
            surf.fill(color)
            sprite.image = surf
        else:
            sprite.image = self.assets["icons"][icon_name]

        return sprite

    def create_entity(self, pos, sprite):
        return self.world.create_entity(
            GameObject(pos, sprite.rect.w, sprite.rect.h), SpriteComponent(sprite)
        )

    def create_derpling(self, pos: Point, facing: Facing, **kwargs):
        sprite = self.create_sprite(pos, env.LEM_WIDTH, env.LEM_HEIGHT, layer=99)
        sprite.image = self.assets["fall"][0]
        entity = self.create_entity(pos, sprite)
        game_object = self.world.component_for_entity(entity, GameObject)
        game_object.facing = facing
        self.world.add_component(entity, AnimationComponent())
        state = DerplingState()
        state.data.update(kwargs)

        self.world.add_component(entity, state)
        self.world.add_component(entity, DescendingDerplingMarker())
        self.world.add_component(entity, MotionComponent(90, env.FALL_SPEED))
        self.world.add_component(entity, LinearMotionMarker())
        self.world.add_component(entity, SoundComponent())
        self.world.add_component(entity, StopWatchComponent())
        return entity

    def create_platform(self, pos: Point, w: float, h: float, is_weak: bool = False):
        icon_name = "platform" if not is_weak else "weak_platform"
        sprite = self.create_sprite(pos, w, h, layer=0, icon_name=icon_name)
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, PlatformComponent())
        if is_weak:
            self.world.add_component(entity, WeakPlatformMarker())

    def create_wall(self, pos: Point, w: float, h: float):
        sprite = self.create_sprite(pos, w, h, layer=0, icon_name="platform")
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, WallComponent())

    def create_teleporter(self, pos: Point, w: float, h: float, properties: dict):
        sprite = self.create_sprite(pos, w, h, icon_name="portal_inactive")
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, TeleporterState(properties))

    def create_trigger(self, pos: Point, w: float, h: float, trigger_id: int):
        sprite = self.create_sprite(pos, w, h, icon_name="trigger")
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, TriggerComponent(trigger_id))

    def create_no_item_zone(self, pos: Point, w: float, h: float):
        sprite = self.create_sprite(pos, w, h, icon_name="invisible")
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, NoItemZoneMarker())

    def create_pickup(self, pos: Point, w: float, h: float, props: dict):
        sprite = self.create_sprite(pos, w, h, icon_name="placeholder")
        entity = self.create_entity(pos, sprite)

        self.world.add_component(
            entity, PickupComponent(props["item_type"], props["amount"])
        )

    def create_item(self, item_type, pos=None):
        if pos is None:
            pos = pygame.mouse.get_pos()
        pos_tile = self.get_tile_coords(pos)
        sprite = self.create_sprite(
            pos_tile, env.GRID_SIZE, env.GRID_SIZE, icon_name=item_type
        )
        sprite.remove(self.sprite_group)
        sprite.add(self.item_group)

        """ If we have an item selected but we switch to another before placing it we can use the item entity created before and just update its properties, instead of creating a new entity """
        if self.item_selected is None:
            eid = self.create_entity(Point(*pos), sprite)
            self.world.add_component(eid, ItemState(item_type))
        else:
            entity = self.world.component_for_entity(self.item_selected, ItemState)
            sp = self.world.component_for_entity(self.item_selected, SpriteComponent)
            sp.sprite.kill()
            entity.type = item_type
            sp.sprite = sprite
            eid = self.item_selected
        return eid

    def create_spawner(self, pos: Point, spawn_free: bool, amount: int):
        sprite = self.create_sprite(
            pos, env.SPAWNER_WIDTH, env.SPAWNER_HEIGHT, icon_name="invisible"
        )
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, SpawnComponent(amount, spawn_free=spawn_free))

    def create_ladder(self, pos: Point, h: float):
        sprite = self.create_sprite(pos, env.LADDER_WIDTH, h, icon_name="ladder")
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, LadderComponent())
        return entity

    def create_goal_trampoline(self, pos: Point, h: float):
        sprite = self.create_sprite(pos, env.LADDER_WIDTH, h, icon_name="trampoline")
        entity = self.create_entity(pos, sprite)
        sprite.kill()
        self.world.add_component(entity, GoalTrampolineMarker())
        return entity

    def create_goal(self, pos: Point, h: float, w: float):
        sprite = self.create_sprite(pos, w, h, icon_name="invisible")
        self.goal_id = entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, GoalComponent())

    def create_camera(self):
        pos = Point(env.SCR_WIDTH // 2, self.map_layer.map_rect.bottom)
        # pos = Point(env.SCR_WIDTH // 2, 1000)
        sprite = Sprite()
        sprite = self.create_sprite(
            pos, env.GRID_SIZE, env.GRID_SIZE, icon_name="invisible"
        )
        entity = self.create_entity(pos, sprite)
        self.world.add_component(entity, CameraComponent())
        self.sprite_group.center(pos)
        return entity

    def create_hud(self):
        builder = HUDBuilder(
            Point(0, env.SCR_HEIGHT - self.assets["hud"]["inventory"].get_height()),
            self.world,
            self.hud_group,
            self.assets,
        )
        builder.build_hud()

    def handle_keyboard_input(self, event):
        if event.key == pygame.K_ESCAPE:
            self.game.pop_scene()
        elif event.key == pygame.K_TAB:
            self.handle_camera_input()

    def handle_camera_input(self):
        camera = self.world.component_for_entity(self.camera, CameraComponent)
        sprite = self.world.component_for_entity(self.camera, SpriteComponent)
        sprite.image = self.assets["hud"]["camera"]
        lemmings = self.world.get_components(DerplingState)
        camera.free_cam = False
        camera.index = (camera.index + 1) % len(lemmings)

    def handle_mouse_input(self, event):
        inventory = self.world.get_components(InventoryComponent, SpriteComponent)
        if event.button == 1:
            for iid, (inv, inv_sprite) in inventory:
                if inv_sprite.rect.collidepoint(event.pos):
                    item_id = int(Point(*event.pos).x // (env.SCR_WIDTH // 10))
                    if LABEL_DATA[item_id] in ["rocket"]:
                        return
                    cur = getattr(inv, LABEL_DATA[item_id])
                    if cur == 0:
                        # play some NOPE sound
                        return
                    self.item_selected = self.create_item(LABEL_DATA[item_id])
                else:
                    if self.item_selected is not None:
                        mouse = [(x // 32) * 32 for x in event.pos]
                        x = mouse[0] + self.map_layer.view_rect.left
                        y = mouse[1] + self.map_layer.view_rect.top

                        noitem_zones = self.world.get_components(
                            SpriteComponent, NoItemZoneMarker
                        )
                        for _, (sprite, noitemzone) in noitem_zones:
                            if sprite.sprite.rect.collidepoint((x, y)):
                                return

                        items = self.world.get_components(GameObject, ItemState)
                        for _, (item_object, _) in items:
                            if item_object.rect.collidepoint((x, y)):
                                return

                        item = self.world.component_for_entity(
                            self.item_selected, ItemState
                        )
                        item_sprite = self.world.component_for_entity(
                            self.item_selected, SpriteComponent
                        ).sprite

                        if item.type == "tnt":
                            self.world.add_component(self.item_selected, TNTComponent())
                            self.world.add_component(
                                self.item_selected, StopWatchComponent()
                            )

                        elif item.type == "ladder":
                            if self.ladder_start_segment is not None:
                                if not mouse[0] == self.ladder_start_segment[0]:
                                    return
                                else:
                                    mouse_y = mouse[1]
                                    start_y = self.ladder_start_segment[1]
                                    step = env.GRID_SIZE
                                    step *= -1 if mouse_y < start_y else 1

                                    current_amount = getattr(inv, item.type)
                                    steps = abs(mouse_y - start_y) // env.GRID_SIZE
                                    if steps > current_amount:
                                        return

                                    for i in range(step, mouse_y - start_y, step):
                                        x = mouse[0] + self.map_layer.view_rect.left
                                        y = (
                                            (start_y + i + self.map_layer.view_rect.top)
                                            // 32
                                        ) * 32
                                        for _, (sprite, noitemzone) in noitem_zones:
                                            if sprite.sprite.rect.collidepoint((x, y)):
                                                self.ladder_start_segment = None
                                                return
                                        segment = self.create_ladder(
                                            Point(x, y), env.GRID_SIZE
                                        )
                                        self.world.add_component(
                                            segment, ItemState(item.type)
                                        )
                                        item_state = self.world.component_for_entity(
                                            segment, ItemState
                                        )
                                        item_state.activate()

                                        current_amount = getattr(inv, item.type)
                                        setattr(inv, item.type, current_amount - 1)
                                    self.ladder_start_segment = None
                            else:
                                self.ladder_start_segment = [
                                    (x // 32) * 32 for x in event.pos
                                ]

                            self.world.add_component(
                                self.item_selected, LadderComponent()
                            )
                        current_amount = getattr(inv, item.type)
                        item.should_activate = True
                        item_sprite.remove(self.item_group)
                        item_sprite.add(self.sprite_group)
                        self.item_selected = None
                        setattr(inv, item.type, current_amount - 1)
                        if current_amount == 1:
                            return
                        self.item_selected = self.create_item(item.type)

        if event.button == 3:
            if self.item_selected is not None:
                sprite = self.world.component_for_entity(
                    self.item_selected, SpriteComponent
                )
                sprite.sprite.kill()
                self.world.delete_entity(self.item_selected)
                self.item_selected = None
                self.item_inventory_id = None
                self.ladder_start_segment = None
            else:
                items = self.world.get_components(
                    GameObject, ItemState, SpriteComponent
                )
                for item_id, (go, item_state, item_sprite) in items:
                    derplings = self.world.get_components(
                        GameObject, DerplingState, MotionComponent, AnimationComponent
                    )
                    for (
                        derpling_id,
                        (
                            derpling_object,
                            derpling_state,
                            derpling_motion,
                            derpling_anim,
                        ),
                    ) in derplings:
                        if "attached-ladder" in derpling_state.data:
                            if derpling_state.data["attached-ladder"] == item_id:
                                derpling_object.pos = Point(
                                    derpling_object.pos.x, derpling_object.pos.y - 10
                                )

                                if self.world.has_component(
                                    derpling_id, LadderDerplingMarker
                                ):
                                    self.world.remove_component(
                                        derpling_id, LadderDerplingMarker
                                    )
                                self.world.add_component(
                                    derpling_id, StopWatchComponent()
                                )
                                self.world.add_component(
                                    derpling_id, DescendingDerplingMarker()
                                )
                                derpling_motion.angle = 90
                                derpling_motion.magnitude = env.FALL_SPEED
                                derpling_anim.change_animation("fall")
                                derpling_state.data["attached-ladder"] = None

                    pos = Point(*event.pos)
                    x = ((pos.x + self.map_layer.view_rect.left) // 32) * 32
                    y = ((pos.y + self.map_layer.view_rect.top) // 32) * 32
                    # 15, 158
                    if go.rect.collidepoint(Point(x, y)):
                        for iid, (inv, inv_sprite) in inventory:
                            current_amount = getattr(inv, item_state.type)
                            setattr(inv, item_state.type, current_amount + 1)
                        item_sprite.sprite.kill()
                        self.world.delete_entity(item_id)
                        return
