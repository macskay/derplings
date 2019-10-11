from zkit.scenes import Scene

import os.path

import pygame


class ImageScene(Scene):
    EVENT_TYPES = {pygame.KEYUP, pygame.MOUSEBUTTONUP}

    def __init__(self, scene_name, image_name, next_scene):
        super(ImageScene, self).__init__(scene_name)
        self.image = pygame.image.load(
            os.path.join("assets", "images", "splash", image_name)
        ).convert()
        self.next_scene = next_scene
        self.rendered = False

    def setup(self):
        pass

    def teardown(self):
        pass

    def resume(self):
        pass

    def draw(self, surface):
        if not self.rendered:
            surface.blit(self.image, self.image.get_rect())
            pygame.display.flip()
            self.rendered = True

    def update(self, delta, events):
        for e in events:
            if e.type in self.EVENT_TYPES:
                self.game.pop_scene()
                self.game.push_scene(self.next_scene)
                self.game.current_scene.update(delta, [])

    def clear(self, surface):
        pass
