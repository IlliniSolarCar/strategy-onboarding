# import simulator tools
from raceEnv import RaceEnv
from route.route import Route
from strategies import Strategy


import numpy as np
import argparse
import json
import os
import sys

dir = os.path.dirname(__file__)
sys.path.insert(0, dir+'/..')   # allow imports from parent directory "onboarding22"


def main(run_infinitely=False, target_speed_file=None, strategy_attributes=None, headless=False):
    headless = True
    strategy = Strategy(parameters=strategy_attributes)

    env = RaceEnv(do_render=not headless, do_print=False, pause_time=0)

    env.set_try_loop(True)

    while True:
        if strategy is not None:
            new_speed = strategy.get_speed(parameters=None, environment=env)
            if new_speed != 30:
                dA = 0
            env.set_target_mph(new_speed)
        done = env.step()
        # env.get_current_leg()
        # get number of legs completed
        if done:
            print(f'average mph: {env.get_average_mph()}', env.get_watthours(), env.get_time(), env.get_miles_earned())
            print(f'average watt hours: {env.get_watthours()}')
            print(f'time: {env.get_time()}')
            print(f'miles earned: {env.get_miles_earned()}')
            print(f'legs completed: {env.get_legs_completed()}')
            env.reset()
            if not run_infinitely:
                break #if you only want to run the simulation once


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Strategy Simulation.')
    parser.add_argument('--run_infinitely', '-ri', action='store_true')
    parser.add_argument('--strategy_file', '-sf', help='name of strategy (see strategies.py). If none, you will be relying only on user input', default=None)
    parser.add_argument('--headless', '-hl', action='store_true')
    args = parser.parse_args()
    strategy_file = args.strategy_file
    strategy_file = 'config/hardcoded_default.json'
    if strategy_file is not None:
        try:
            strategy = json.load(open(strategy_file))
        except:
            raise Exception(f'Error: Could not read strategy file {strategy_file}'
                            'Check the path and make sure it is a json file')

    main(run_infinitely=args.run_infinitely, strategy_attributes=strategy, headless=args.headless)
