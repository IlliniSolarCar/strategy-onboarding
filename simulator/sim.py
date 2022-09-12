# import simulator tools
from datetime import timedelta
from raceEnv import RaceEnv
from route.route import Route


'''
This simulator is designed to be controlled in 3 ways:
1. Keyboard inputs: Create the RaceEnv object with load=None and do_render=True.
2. Preprogrammed inputs: Create the RaceEnv object with load=None and use env.set_target_mph() and env.set_try_loop().
3. Replay inputs from file: Drop your file in simulator/logs/ and create the RaceEnv object with load='FILE NAME HERE'. 

To run: Click the Play [ ▶️ ] button in the top right of VS Code, or run in terminal: ` python sim.py `.

Tip: Some functions like RaceEnv() and set_target_mph() will display more information when you hover over the code.
'''


def main():
    env = RaceEnv(load=None, save=True, do_render=True, do_print=True)

    while True:
        
        '''Preprogrammed input: Uncomment the following line to make the car drive at 35mph for the first leg of the race, 
        then 45mph for the rest. Setters also exist for acceleration and deceleration.'''
        # if(env.get_leg_index() == 0):
        #     env.set_target_mph(35)
        # else:
        #     env.set_target_mph(45)

        '''Preprogrammed input: Uncomment the following line to make the car attempt any loops it encounters. This might not
        always be a good idea because loops only count if finished on time. No partial credit means time and energy can be wasted
        attempting an impossible loop. For best results, set try loop to True or False depending on where you are in the race. '''
        # env.set_try_loop(True)


        '''Data: Uncomment the following 3 lines to print the solar irradiance for a flat panel at 1 mile and 1 hour later. 
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
            break   #break out of the while loop if the simulation is done



if __name__ == "__main__":
    main()