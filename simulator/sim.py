# import simulator tools
from raceEnv import RaceEnv
from route.route import Route


def main():
    env = RaceEnv(do_render=False, do_print=False)

    env.set_try_loop(True)

    while True:
        
        # action['target_mph'] = np.random.randint(6, 35)
        env.set_target_mph(30)
        done = env.step()
        
        if done:
            print(env.get_target_mph(), env.get_watthours(), env.get_time(), env.get_miles_earned())
            print(env.get_legs_attempted())
            env.reset()
            break #if you only want to run the simulation once
    

if __name__ == "__main__":
    main()