This folder contains .csv files for the inputs of previous simulations.
When creating a RaceEnv, set the load= parameter to the csv file name to rerun
the simulation with exactly the same inputs. 

Example:
env = RaceEnv(load='368mi_5400W.csv', do_render=True, do_print=True)
