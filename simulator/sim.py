# import simulator tools
from raceEnv import RaceEnv
from route.route import Route

import numpy as np

def main():
    env = RaceEnv(do_render=True, do_print=True, steps_per_render=3)

    while True:
        
        
        # env.set_target_mph(35)


        done = env.step()
        
        if done:
            print(f"Miles earned: {env.get_miles_earned()}")
            print(f"Average mph: {env.get_average_mph()}")
            print(f"Energy left: {env.get_watthours()}")
            print(f"Legs attempted: {env.get_legs_attempted()}")
            print(f"Legs completed: {env.get_legs_completed()}")
            env.reset()
            break #if you only want to run the simulation once

if __name__ == "__main__":
    main()