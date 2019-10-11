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


class TeleporterState:
    states = [
        "inactive",
        "active",
        "open",
        "begin"
    ]

    transitions = [
        {"trigger": "init", "source": "begin", "dest": "inactive"},
        {"trigger": "activate", "source": "inactive", "dest": "active"},
        {"trigger": "open", "source": "active", "dest": "open"},
    ]

    def __init__(self, properties):
        self.properties = properties
        self.counter_part_eid = None
        self.trigger_eid = None
        self.count = 0
        self.machine = Machine(model=self,
                               states=self.states,
                               transitions=self.transitions,
                               initial="begin")


@dataclass
class TriggerComponent:
    """ Marker class for TriggerComponent """
    tid: int
    active: bool = False


class TeleporterProcessor(Processor):
    def __init__(self):
        super(TeleporterProcessor, self).__init__()

    def process(self, scene, delta):
        for eid, state in self.world.get_component(TeleporterState):
            self.process_map[state.state](self, scene, delta, eid)

    def activate(self, eid, scene):
        teleport_sprite = self.world.component_for_entity(eid, SpriteComponent)
        teleport_sprite.sprite.image = scene.assets["icons"]["portal_active"]

        teleport = self.world.component_for_entity(eid, TeleporterState)
        teleport.activate()

    def open(self, eid):
        teleport = self.world.component_for_entity(eid, TeleporterState)
        teleport.open()

    def process_begin(self, scene, delta, eid):
        triggers = self.world.get_component(TriggerComponent)
        teleport = self.world.component_for_entity(eid, TeleporterState)
        all_teleports = self.world.get_component(TeleporterState)
        for trigger_eid, trigger in triggers:
            if trigger.tid == teleport.properties["tpid"]:
                teleport.trigger_eid = trigger_eid

        for other_tp_id, other_teleport in all_teleports:
            if teleport.properties["counter_part"] == other_teleport.properties["tpid"]:
                teleport.counter_part_eid = other_tp_id
        teleport.init()

    def process_active(self, scene, delta, eid):
        teleport = self.world.component_for_entity(eid, TeleporterState)
        counter_part = self.world.component_for_entity(teleport.counter_part_eid, TeleporterState)
        # both checks need to be done, since one teleporter will do the switch first and then be in open-state, so the counter_part needs to check for open
        if counter_part.is_active() or counter_part.is_open():
            self.open(eid)

    def process_open(self, scene, delta, eid):
        teleport = self.world.component_for_entity(eid, TeleporterState)

        if teleport.count >= teleport.properties["amount"]:
            teleport_sprite = self.world.component_for_entity(eid, SpriteComponent)
            teleport_sprite.sprite.kill()
            self.world.delete_entity(eid)

    def process_inactive(self, scene, delta, eid):
        teleport = self.world.component_for_entity(eid, TeleporterState)
        trigger = self.world.component_for_entity(teleport.trigger_eid, TriggerComponent)
        if trigger.active:
            self.activate(eid, scene)

    process_map = {
        "open": process_open,
        "active": process_active,
        "inactive": process_inactive,
        "begin": process_begin
    }
