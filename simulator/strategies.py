# A list of potential strategies
# In each strategy, you may put default values in its init
# Then when get_speed_with_parameters is called, you have access to both any parameters the user
# wants to pass in, and the environment.
# Create your own strategies by making a subclass here. All they need is the following three steps:
# 1) an __init__ method that lets the user initialize the class. This will change depending on what default information is needed
# 2) a get_speed_with_parameters(self, parameters, environment) method with parameters as a dictionary with any values (could be None),
#    and an environment object (which is a raceEnv object)
# 3) You need to register it as part of the init method in the strategy superclass.
#    You can do that like this:
#    if self.strategy_name == 'my_strategy':
#        self.strategy = self.MyStrategy(my_default_speed=13, my_default_accel=12)
#    You need to change my_default_speed and  my_default_accel to whatever is needed to initialize your specific strategy


from typing import Optional
import numpy as np
import csv
import os
import sys

dir = os.path.dirname(__file__)
sys.path.insert(0, dir+'/../')   #allow imports from parent directory "onboarding22"

from util import meters2miles


class Strategy:
    # This is a bit ugly because nested classes cannot extend parent classes.
    #  However, as long as the nested classes have the get_speed_with_parameters method in some
    # form, this part of the program should work.
    class RandomStrategy:
        def __init__(self, default_min_speed: int, default_max_speed: int):
            self.min_speed_default = default_min_speed
            self.max_speed_default = default_max_speed

        def get_random_speed(self, min_speed: Optional[int] = None, max_speed: Optional[int] = None):
            min_speed = min_speed if min_speed is not None else self.min_speed_default
            max_speed = max_speed if max_speed is not None else self.max_speed_default
            return np.random.randint(min_speed, max_speed)

        def get_speed_with_parameters(self, parameters: Optional[dict] = None, environment=None):

            min_speed = parameters['min_speed'] if parameters is not None and 'min_speed' in parameters else None
            max_speed = parameters['min_speed'] if parameters is not None and 'min_speed' in parameters else None
            return self.get_random_speed(min_speed, max_speed)

    class LazyStrategy:
        def __init__(self, default_target_speed: int):
            self.default_target_speed = default_target_speed

        def get_lazy_speed(self, target_speed: Optional[int] = None):
            target_speed = target_speed if target_speed is not None else self.default_target_speed
            return target_speed

        def get_speed_with_parameters(self, parameters: Optional[dict] = None, environment=None):
            target_speed = parameters['target_speed'] if parameters is not None and 'target_speed' in parameters else None
            return self.get_lazy_speed(target_speed=target_speed)

    class HardcodedStrategy:
        # These IDX is what index of the csv file it is
        # leg, distance, target_speed
        def __init__(self, csv_file_name: str, default_speed : int = 30):
            self.leg_idx = 0
            self.distance_idx = 1
            self.speed_idx = 2

            self.default_speed = default_speed

            with open(csv_file_name, newline='') as csvfile:
                self.all_commands = list(csv.reader(csvfile, delimiter=','))[1:]
                self.all_commands = [[x.strip() for x in row] for row in self.all_commands]
                for i in range(0, len(self.all_commands)):
                    for j in range(0, len(self.all_commands[i])):
                        idxs_to_convert = [1, 2]
                        if j in idxs_to_convert:
                            self.all_commands[i][j] = int(self.all_commands[i][j])


                #self.all_commands = list(map(lambda l: map(lambda v: int(v) if v == 1 or v == 2 else v, l), self.all_commands))
            self.leg_name_to_command = {}
            for command in self.all_commands:
                if command[self.leg_idx] not in self.leg_name_to_command:
                    self.leg_name_to_command[command[self.leg_idx]] = []

                self.leg_name_to_command[command[self.leg_idx]].append(command)
            for leg_name in list(self.leg_name_to_command.keys()):
                self.leg_name_to_command[leg_name] = list(sorted(self.leg_name_to_command[leg_name], key=lambda v: v[self.distance_idx]))
                if len(list(filter(lambda v: v[self.distance_idx] == 0, self.leg_name_to_command[leg_name])))== 0:
                    # we add a default condition if the user didn't specify what to do at distance 0
                    self.leg_name_to_command[leg_name].insert(0, [leg_name, 0, self.default_speed])

        def get_hardcoded_speed(self, leg_name, distance_into_leg):
            if leg_name not in self.leg_name_to_command:
                return self.default_speed
            commands = self.leg_name_to_command[leg_name]
            # len(commands) should never be 0
            if len(commands) == 1:
                return commands[0][self.speed_idx]
            else:
                if commands[1][self.distance_idx] <= distance_into_leg:
                    target_speed = commands[1][self.speed_idx]
                    self.leg_name_to_command[leg_name].pop(0)
                    return target_speed
                else:
                    return commands[0][self.speed_idx]

        def get_speed_with_parameters(self, parameters, environment):
            leg_name = environment.current_leg['name'].strip('.')[0]
            loop_index = environment.get_loop_index()
            if loop_index != 0:
                # If we are on the second topeka loop, this would look like AL2
                leg_name = f'{leg_name}L{loop_index}'
            distance_into_leg = meters2miles(environment.leg_progress)
            return self.get_hardcoded_speed(leg_name=leg_name, distance_into_leg=distance_into_leg)
            #return get_speed(leg_name=environment)


    def __init__(self, parameters: dict):
        self.strategy_name = parameters['name']
        # You need to add new strategies to this list
        if self.strategy_name == 'random':
            self.strategy = self.RandomStrategy(default_min_speed=parameters['min_speed'], default_max_speed=parameters['max_speed'])
        if self.strategy_name == 'lazy':
            self.strategy = self.LazyStrategy(default_target_speed=parameters['target_speed'])
        if self.strategy_name == 'hardcoded':
            self.strategy = self.HardcodedStrategy(csv_file_name=parameters['csv_file_name'])


    def get_speed(self, parameters: Optional[dict] = None, environment=None) -> int:
        speed = self.strategy.get_speed_with_parameters(parameters, environment)
        min_mph = environment.get_min_mph()
        max_mph = environment.get_max_mph()
        if environment is not None and min_mph > speed:
            return min_mph
        elif environment is not None and max_mph < speed:
            return max_mph
        return speed
