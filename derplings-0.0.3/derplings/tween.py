from esper import Processor


class TweenProcessor(Processor):

    def __init__(self):
        super(TweenProcessor, self).__init__()

    def process(self, scene, delta):
        for entity, tween in self.world.get_component(Tween):
            comp = self.world.component_for_entity(tween.entity,
                                                   tween.component)
            tween.elapsed_ms += delta
            if tween.elapsed_ms > tween.easing_fn.duration:
                self.world.delete_entity(entity)
            else:
                setattr(comp, tween.attribute,
                        tween.easing_fn.ease(tween.elapsed_ms))


class Tween:

    def __init__(self, entity, easing_fn, component, attribute):
        self.entity = entity
        self.easing_fn = easing_fn
        self.elapsed_ms = 0
        self.component = component
        self.attribute = attribute
