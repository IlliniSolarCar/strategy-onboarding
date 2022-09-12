# import simulator tools
from xmlrpc.server import SimpleXMLRPCRequestHandler
from raceEnv import RaceEnv
from route.route import Route

import numpy as np
import argparse
from strategies import Strategy

def main(run_infinitely=False, target_speed_file=None, strategy_attributes=None):
    strategy = Strategy(parameters=strategy_attributes)



    env = RaceEnv(do_render=True, do_print=False, pause_time=0)
    
    env.set_try_loop(True)

    while True:
        if strategy is not None:
            new_speed = strategy.get_speed(parameters=None)
            env.set_target_mph(new_speed)

        if target_speed_file is not None:
            env.set_target_mph(np.random.randint(30, 40))
        done = env.step()
        
        if done:
            print(env.get_average_mph(), env.get_watthours(), env.get_time(), env.get_miles_earned())
            print(env.get_legs_attempted())
            print(env.get_legs_completed())
            env.reset()
            if not run_infinitely:
                break #if you only want to run the simulation once
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Strategy Simulation.')
    parser.add_argument('--run_infinitely', '-ri', action='store_true')
    parser.add_argument('--strategy', '-s', help='name of strategy (see strategies.py)')
    args = parser.parse_args()
    strategy_attributes = {
        'name': 'random',
        'min_speed_default': 20,
        'max_speed_default': 40
    }
    strategy_attributes = {
        'name': 'lazy',
        'default_target_speed': 30
    }
    main(run_infinitely=args.run_infinitely, strategy_attributes=strategy_attributes)