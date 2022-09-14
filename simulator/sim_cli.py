'''
This simulator is designed to be controlled in 3 ways:
1. Keyboard inputs: Create the RaceEnv object with load=None and do_render=True.
2. Preprogrammed inputs: Create the RaceEnv object with load=None and use env.set_target_mph() and env.set_try_loop().
3. Replay inputs from file: Drop your file in simulator/logs/ and create the RaceEnv object with load='FILE NAME HERE'. 

To run: Click the Play [ ▶️ ] button in the top right of VS Code, or run in terminal: ` python sim.py `.

Tip: Some functions like RaceEnv() and set_target_mph() will display more information when you hover over the code.
'''

# import simulator tools
from datetime import timedelta
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




def main(run_infinitely=False, strategy_attributes=None, render=False, save=False, load=None, do_print=False):
    strategy = Strategy(parameters=strategy_attributes) if strategy_attributes is not None else None

    env = RaceEnv(load=load, save=save, do_render=render, do_print=do_print)

    while True:

        if strategy is not None:
            new_speed = strategy.get_speed(parameters=None, environment=env)
            env.set_target_mph(new_speed)
        done = env.step()


        '''Preprogrammed input: Uncomment the following line to make the car attempt any loops it encounters. This might not
        always be a good idea because loops only count if finished on time. No partial credit means time and energy can be wasted
        attempting an impossible loop. For best results, set try loop to True or False depending on where you are in the race. '''
        env.set_try_loop(True)


        '''Data: Uncomment the following 4 lines to print the solar irradiance for a flat panel at 1 mile and 1 hour later. 
        Similar functions exist for headwind, slope, elevation, and car logs.
        '''
        # mile_later = env.get_leg_progress() + 1
        # hour_later = env.get_time() + timedelta(hours=1)
        # irradiance = env.get_solar_flat(dist=mile_later, time=hour_later)
        # print(irradiance)


        '''Following chunk of code updates the simulation and prints out results when done'''
        done = env.step()
        if done:
            print(f"Miles earned: {env.get_miles_earned()}")
            print(f"Energy left: {env.get_watthours()}")
            print(f"Average mph: {env.get_average_mph()}")
            print(f"Stadard deviation mph: {env.get_stddev_mph()}")
            print(f"Legs attempted: {env.get_legs_attempted()}")
            print(f"Legs completed: {env.get_legs_completed()}")

            env.reset()
            if not run_infinitely:
                break #if you only want to run the simulation once


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Strategy Simulation.')
    parser.add_argument('--run_infinitely', '-ri', action='store_true')
    parser.add_argument('--strategy_file', '-sf', help='name of strategy (see strategies.py). If none, you will be relying only on user input', default=None)
    parser.add_argument('--render', '-r', action='store_true', help='display graphical representation of simulation')
    parser.add_argument('--save', '-s', action='store_true', help='save to log directory')
    parser.add_argument('--load', '-l', help='load speeds from previous run.', default=None)
    parser.add_argument('--print', '-p', action='store_true', help='prints more information to screen')
    args = parser.parse_args()

    # If you are too lazy to use these arguments in CL every time, override them here. 
    # For example say this to override args.save being false by default
    # args.save = True

    strategy_file = args.strategy_file
    if strategy_file is not None:
        try:
            strategy = json.load(open(strategy_file))
        except:
            raise Exception(f'Error: Could not read strategy file {strategy_file}'
                            'Check the path and make sure it is a json file')
    else:
        strategy = None

    main(run_infinitely=args.run_infinitely, strategy_attributes=strategy, render=args.render, save=args.save, load=args.load, do_print=args.print)
