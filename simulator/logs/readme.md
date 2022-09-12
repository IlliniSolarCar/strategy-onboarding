This folder contains .csv files for the inputs of previous simulations.
When creating a RaceEnv, set the `load=` parameter to the csv file name to rerun
the simulation with exactly the same inputs. You can also generate your own .csv files
and place them here with the target_mph, acceleration, deceleration, and try_loop for 
every time step.

Example:
`env = RaceEnv(load='368mi_2868W.csv', do_render=True, do_print=True)`


To populate this folder with saved inputs, create a RaceEnv with the parameter `save=True`.

Example:
`env = RaceEnv(save=True, do_render=True, do_print=True)`