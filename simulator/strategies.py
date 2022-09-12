from typing import Optional
import numpy as np


class Strategy:
    # This is a bit ugly because nested classes cannot extend parent classes.
    #  However, as long as the nested classes have the get_speed_with_parameters method in some
    # form, this part of the program should work.
    class RandomStrategy:
        def __init__(self, min_speed_default : int, max_speed_default : int):
            self.min_speed_default = min_speed_default
            self.max_speed_default = max_speed_default

        def get_speed(self, min_speed: Optional[int] = None, max_speed: Optional[int] = None):
            min_speed = min_speed if min_speed is not None else self.min_speed_default
            max_speed = max_speed if max_speed is not None else self.max_speed_default
            return np.random.randint(min_speed, max_speed)

        def get_speed_with_parameters(self, parameters: Optional[dict] = None):

            min_speed = parameters['min_speed'] if parameters is not None and 'min_speed' in parameters else None
            max_speed = parameters['min_speed'] if parameters is not None and 'min_speed' in parameters else None
            return self.get_speed(min_speed, max_speed)

    class LazyStrategy:
        def __init__(self, default_target_speed: int):
            self.default_target_speed = default_target_speed

        def get_speed(self, target_speed: Optional[int] = None):
            target_speed = target_speed if target_speed is not None else self.default_target_speed
            return target_speed

        def get_speed_with_parameters(self, parameters: Optional[dict] = None):
            target_speed = parameters['target_speed'] if 'target_speed' in parameters else None
            return self.get_speed(target_speed=target_speed)

    def __init__(self, parameters: dict):
        self.strategy_name = parameters['name']
        # You need to add new strategies to this list
        if self.strategy_name == 'random':
            self.strategy = self.RandomStrategy(min_speed_default=parameters['min_speed_default'], max_speed_default=parameters['max_speed_default'])
        if self.strategy_name == 'lazy':
            self.strategy = self.LazyStrategy(default_target_speed=parameters['default_target_speed'])

    def get_speed(self, parameters: Optional[dict] = None) -> int:
        return self.strategy.get_speed(parameters)
