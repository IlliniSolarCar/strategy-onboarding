# import simulator tools
from raceEnv import RaceEnv
from route.route import Route

import numpy as np

def main():
    env = RaceEnv(do_render=True, do_print=False)

    env.set_try_loop(True)

    while True:
        
        env.set_target_mph(np.random.randint(30, 40))
        done = env.step()
        
        if done:
            print(env.get_average_mph(), env.get_watthours(), env.get_time(), env.get_miles_earned())
            print(env.get_legs_attempted())
            print(env.get_legs_completed())
            env.reset()
            break #if you only want to run the simulation once
    

if __name__ == "__main__":
    main()