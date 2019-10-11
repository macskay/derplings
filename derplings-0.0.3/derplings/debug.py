import pygame
from planar import Point

from .datacl import Facing
from .item import ItemState
from .animation import AnimationComponent


def handle_debug_input(self, event):
    if event.type == pygame.KEYUP:
        if event.key == pygame.K_1:
            self.item_selected = self.create_item("umbrella")
        elif event.key == pygame.K_2:
            self.item_selected = self.create_item("stopsign")
        elif event.key == pygame.K_3:
            self.item_selected = self.create_item("trampoline")
        elif event.key == pygame.K_4:
            self.item_selected = self.create_item("jetpack")
        elif event.key == pygame.K_5:
            self.item_selected = self.create_item("grow")
        elif event.key == pygame.K_6:
            self.item_selected = self.create_item("shrink")
        elif event.key == pygame.K_q:
            print(self.no_derplings)

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            if self.item_selected is None:
                pos = Point(
                    event.pos[0] + self.map_layer.view_rect.left,
                    event.pos[1] + self.map_layer.view_rect.top,
                )
                self.sounds["sounds"]["explode"].play(loops=0, maxtime=0, fade_ms=0)
                self.create_derpling(pos, Facing.RIGHT)
            else:
                item = self.world.component_for_entity(self.item_selected, ItemState)
                if item.is_active():
                    self.item_selected = None
        elif event.button == 3:
            pos = Point(
                event.pos[0] + self.map_layer.view_rect.left,
                event.pos[1] + self.map_layer.view_rect.top,
            )
            self.sounds["sounds"]["explode"].play(loops=0, maxtime=0, fade_ms=0)
            derp_id = self.create_derpling(pos, 0)
            self.world.component_for_entity(derp_id, AnimationComponent).mirror = False
