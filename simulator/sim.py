# import simulator tools
from raceEnv import RaceEnv
from route.route import Route


def main():
    env = RaceEnv(render=True)

    env.action = {
        "target_mph": 54,
        "acceleration": 0.5,
        "deceleration": -0.5,
        "try_loop": False,
    }

    while True:
        
        # action['target_mph'] = np.random.randint(6, 35)
        done = env.step(env.action)
        
        if done == True:
            break
    

if __name__ == "__main__":
    main()