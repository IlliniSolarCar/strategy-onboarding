# import simulator tools
from datetime import timedelta
from raceEnv import RaceEnv
from route.route import Route


'''
This file is designed to run the GUI with keyboard controls.

To run: Click the Play [ ▶️ ] button in the top right of VS Code, or run in terminal: ` python sim_key.py `.
'''


def main():
    env = RaceEnv(load=None, save=True, do_render=True, do_print=True)

    while True:
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