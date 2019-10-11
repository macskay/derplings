from transitions import Machine
from pygame.sprite import Sprite
import pygame

from esper import Processor
from planar import Point
from dataclasses import dataclass

from . import env
from .gfx import SpriteComponent
from .movement import StopWatchComponent, MotionComponent
from .datacl import PlatformComponent, GameObject
from .animation import AnimationComponent
from .mechanics import LadderComponent
from .inventory import InventoryComponent


class ItemState:
    states = ["inactive", "active"]

    transitions = [{"trigger": "activate", "source": "inactive", "dest": "active"}]

    def __init__(self, item_type, random=False):
        self.type = item_type
        self.should_activate = False
        self.random = random
        self.machine = Machine(
            model=self,
            states=self.states,
            transitions=self.transitions,
            initial="inactive",
        )


class ItemProcessor(Processor):
    def __init__(self):
        super(ItemProcessor, self).__init__()

    def process(self, scene, delta):
        for eid, state in self.world.get_component(ItemState):
            self.process_map[state.state](self, scene, delta, eid)

    def activate(self, eid, scene):
        item_sprite = self.world.component_for_entity(eid, SpriteComponent)
        item_sprite.sprite.image.set_alpha(128)

        item_object = self.world.component_for_entity(eid, GameObject)
        item_state = self.world.component_for_entity(eid, ItemState)
        x = ((item_object.pos.x + scene.map_layer.view_rect.left) // 32) * 32
        y = ((item_object.pos.y + scene.map_layer.view_rect.top) // 32) * 32
        item_object.pos = Point(x, y)
        item_state.activate()

    def process_active(self, scene, delta, eid):
        """
        item = self.world.component_for_entity(eid, GameObject)
        sprite = self.world.component_for_entity(eid, SpriteComponent)
        pos = pygame.mouse.get_pos()
        x = (pos[0] + scene.map_layer.view_rect.left) // 32 * 32
        y = (pos[1] + scene.map_layer.view_rect.top) // 32 * 32
        pos_tile = Point(x, y)

        state = pygame.mouse.get_pressed()
        if state[2]:
            if pos_tile == item.pos:
                inventory = self.world.get_component(InventoryComponent)
                item_state = self.world.component_for_entity(eid, ItemState)
                if item_state.type == "ladder":
                    ladder = self.world.component_for_entity(eid, LadderComponent)
                    if ladder.in_use:
                        print("in_use")
                        return
                for iid, inv in inventory:
                    current = getattr(inv, item_state.type)
                    setattr(inv, item_state.type, current + 1)
                sprite.sprite.kill()

                self.world.remove_component(eid, GameObject)
                self.world.remove_component(eid, SpriteComponent)
                self.world.remove_component(eid, ItemState)
        """
        pass

    def process_inactive(self, scene, delta, eid):
        item = self.world.component_for_entity(eid, GameObject)
        item_state = self.world.component_for_entity(eid, ItemState)

        pos = pygame.mouse.get_pos()
        x = (pos[0] // 32) * 32
        y = (pos[1] // 32) * 32
        pos_tile = Point(x, y)
        item.pos = pos_tile

        if item_state.should_activate:
            self.activate(eid, scene)

    process_map = {"active": process_active, "inactive": process_inactive}


@dataclass
class PickupComponent:
    item_type: str
    amount: int
