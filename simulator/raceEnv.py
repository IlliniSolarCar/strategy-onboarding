from datetime import timedelta
from math import isnan
from re import L
import time
from tkinter import ROUND
import gym
from gym import spaces
import numpy as np
import json
import matplotlib.pyplot as plt
import sys, os

dir = os.path.dirname(__file__)
sys.path.insert(0, dir+'/../')   #allow imports from parent directory "onboarding22"

from simulator.blit import BlitManager
from route.route import *
from util import *



class RaceEnv(gym.Env):
    '''Simulation of ASC using an OpenAI gym environment. Call .step(action) to update simulation.
    Inputs can be entered in 3 ways: from a keyboard using the render window, from the program by calling .set functions, and from previously loaded
    inputs by specifying a .csv file.
       
        load: string of the name of the .csv file to load inputs from. If not filled, inputs will come from calling set functions or the keyboard.
        save: boolean of whether to save the simulation into a .csv file to be loaded and rerun later.
        save_name: string to name the saved .csv file. If left empty, name is auto generated.
        do_render: boolean whether to display the animated graphs
        do_print: boolean of whether to print progress reports along the race
        car: name of the car to simulate. Cars are stored as .json in the cars/ folder.
        route: name of the route to simulate. Routes are stored as .route in the route/save_routes folder.

        Note: do not use file extensions (eg .csv) when specifying file names. They will be added automatically.
    '''

    def __init__(self, load=None, save=True, save_name='', do_render=True, do_print=True, car="brizo_fsgp22", route="ind-gra_2022,7,9-10_5km_openmeteo"):

        cars_dir = os.path.dirname(__file__) + '/../cars'
        with open(f"{cars_dir}/{car}.json", 'r') as props_json:
            self.car_props = json.load(props_json)
        
        route_obj = Route.open(route)
        self.legs = route_obj.leg_list

        self.save = save
        self.save_name = save_name

        self.is_keyboard = False

        self.pause_time = 1e-6
        self.dist_behind = 3
        self.dist_ahead = 7

        self.do_print = do_print
        self.do_render = do_render
        
        self.timestep = 5 #5 second intervals

        self.observation_spaces= spaces.Dict({
            "dist_traveled": spaces.Box(0, float('inf')),
            "slope": spaces.Box(-10, 10)
        })

        #action is setting the target speed and choosing whether to try loops
        self.action_space = spaces.Dict({
            "target_mph": spaces.Box(mph2mpersec(self.car_props['min_mph']), mph2mpersec(self.car_props['max_mph'])),
            "acceleration": spaces.Box(0, self.car_props['max_accel']),
            "deceleration": spaces.Box(self.car_props['max_decel'], 0),
            "try_loop": spaces.Discrete(2),
        })

        self.action = {
            "target_mph": self.car_props['max_mph'],
            "acceleration": self.car_props['max_accel'],
            "deceleration": self.car_props['max_decel'],
            "try_loop": False,
        }

        if(load is not None):
            self.load_name = load
            file_path = f"{dir}/simulator/logs/{load}.csv"
            try:
                self.load = pd.read_csv(file_path)
            except:
                raise FileNotFoundError(file_path)
            self.printc(f"Loaded input from file: {file_path}")
        else:
            self.load = None

        self.legs_completed_names = []
        self.legs_completed = 0
        self.current_leg = self.legs[0]
        self.leg_index = 0
        self.leg_progress = 0
        self.speed = 0
        self.energy = self.car_props['max_watthours']*3600  #joules left in battery
        self.brake_energy = 0                               #joules dissipated in mechanical brakes
        self.time = self.legs[0]['start'] #datetime object
        self.miles_earned = 0
        self.motor_power = 0
        self.array_power = 0
        
        self.try_loop = False
        self.done = False

        self.next_stop_dist = 0
        self.next_stop_index = 0
        self.limit = None
        self.next_limit_dist = 0
        self.next_limit_index = 0

        self.sim_step = 0
        self.transition = False
        self.pause = False
        self.steps_per_render = 1

        self.reset()
        if(self.do_render):
            self.render_init()

        self.printc(f"Start race at {self.time}")


    def printc(self, message):
        if(self.do_print):
            print(f"(RaceEnv) {message}")
    

    def reset_leg(self):
        self.leg_progress = 0
        self.speed = 0
        self.next_stop_dist = 0
        self.next_stop_index = 0
        self.limit = None
        self.next_limit_dist = 0
        self.next_limit_index = 0
        self.distwindow_l = 0
        self.distwindow_r = miles2meters(self.dist_behind + self.dist_ahead)
        limit_dist_pts, limit_pts = self.current_leg['speedlimit']
        self.limit_dist_pts, self.limit_pts = ffill(limit_dist_pts, limit_pts)

        self.log['leg_names'].append(self.current_leg['name'])
        for item in self.log:
            if(item != 'leg_names'):
                self.log[item].append([])
        

    def reset(self):
        self.transition = True
        # We need the following line to seed self.np_random
        super().reset()

        self.leg_index = 0
        self.current_leg = self.legs[0]
        self.legs_completed = 0
        self.time = self.legs[0]['start']
        self.energy = self.car_props['max_watthours']*3600
        self.miles_earned = 0
        self.done = False

        self.log = {
            "leg_names": [],
            "times": [],
            "dists": [],
            "speeds": [],
            "target_mphs": [],
            "accelerations": [],
            "decelerations": [],
            "try_loops": [],
            "energies": [],
            "motor_powers": [],
            "array_powers": [],
        }

        self.reset_leg()



    def charge(self, time_length:timedelta):
        '''
        Updates energy and time, simulating the car sitting in place tilting its array optimally towards the sun for a period of time
        '''
        time_length = max(timedelta(0), time_length)

        leg = self.legs[self.leg_index]
        end_time = self.time + time_length

        timestep = 5
        times = np.arange(self.time.timestamp(), end_time.timestamp()+timestep, step=timestep)
        irradiances = np.array([leg['sun_tilt'](self.leg_progress, time) for time in times])
        irradiances = np.nan_to_num(irradiances)
        powers = irradiances * self.car_props['array_multiplier']

        before = self.energy

        self.energy += powers.sum() * timestep
        self.energy = min(self.energy, self.car_props['max_watthours']*3600)
        
        self.printc(f"Charged {round((self.energy - before)/3600.)}W. Now {self.time}")

       
        self.time = self.time + time_length


    def process_leg_finish(self):
        '''
        An absolute mess of logic that processes loops, holdtimes, charging hours.
        Assumes the race always ends in a stage stop, and there are never 2 loops in a row.
        '''
        leg = self.legs[self.leg_index]

        if(self.time > leg['close'] and (leg['type']=='loop' or leg['end']=='stagestop')):
            self.printc("Earned 0 miles")
        else:
            self.printc(f"Earned {round(meters2miles(leg['length']))} miles")
            self.miles_earned += meters2miles(leg['length']) #earn miles if completed on time
            self.legs_completed += 1
            self.legs_completed_names.append(leg['name'])

        is_last_leg = self.leg_index == (len(self.legs) - 1)
        if(is_last_leg and leg['type']=='base'):
            self.done = True
            self.printc("Ended on a base leg. Completed entire route!")
            return

        holdtime = timedelta(minutes=15) if (leg['type']=='loop') else timedelta(minutes=45)

        if(self.time < leg['open']):    #if arrive too early, wait for checkpoint/stagestop to open
            self.charge(leg['open'] - self.time)

        if(leg['end'] == 'checkpoint'):

            self.charge(min(leg['close'] - self.time, holdtime)) #stay at checkpoint/stagestop for the required holdtime, or it closes

            next_leg = self.legs[self.leg_index+1] #ended at a checkpoint not stagestop, so there must be another leg

            if(self.time < leg['close']): #there's still time left after serving required hold time

                if(self.try_loop and (leg['type']=='loop' or next_leg['type']=='loop')): #there's a loop and user wants to do it
                    if(leg['type']=='loop'):
                        self.printc(f"Redo loop: {leg['name']} at {self.time}")
                        return
                    else:
                        self.printc(f"Try the upcoming loop: {next_leg['name']} at {self.time}")
                        self.leg_index += 1
                        return
                else:
                    
                    while next_leg['type']=='loop':
                        self.leg_index += 1
                        next_leg = self.legs[self.leg_index]

                    self.charge(next_leg['start'] - self.time) #wait for release time                        

                    self.printc(f"End at checkpoint, move onto next base leg: {next_leg['name']} at {self.time}")
                    return

            else: #checkpoint closed, need to move onto next base leg. To get to this point self.time is the close time.
                # if(leg['type']=='loop'):
                #     self.printc(f"Did not arrive before close: {leg['name']}")

                if(next_leg['type']=='loop'):
                    self.printc('Next leg is a loop, skipping to the base leg after that')
                    self.leg_index += 2
                    return
                else:
                    while next_leg['type']!='base': #pick the next base leg
                        self.leg_index += 1
                        next_leg = self.legs[self.leg_index]
                    self.leg_index += 1
                    self.printc(f"Start the upcoming base leg: {next_leg['name']} at {self.time}")
                    # self.printc(self.legs[self.leg_index])
                    return

        else:                   #leg ends at a stage stop.
                
            if(self.time < leg['close']): #arrived before stage close.

                self.charge(min(leg['close'] - self.time, holdtime)) #stay at stagestop for the required holdtime, or it closes


                if(self.time < leg['close']): #stage hasn't closed yet after serving hold time

                    if(self.try_loop and leg['type']=='loop'):
                        self.printc(f"Completed the loop and trying it again: {leg['name']} at {self.time}")
                        self.charge(timedelta(minutes=15))
                        return

                    if(is_last_leg): #for final leg to get to this point, must be a loop and try_loop==False
                        self.printc('Completed the loop at the end of the race, and will not be attemping more.')
                        self.charge(leg['close'] - self.time)                        #charge until stage close
                        self.charge(timedelta(hours=EVENING_CHARGE_HOURS))    #evening charging
                        self.done = True
                        return

                    next_leg = self.legs[self.leg_index+1]
                    if(self.try_loop and next_leg['type']=='loop'):
                        self.printc(f"Completed the base leg and trying the next loop: {next_leg['name']}")
                        self.charge(timedelta(minutes=15))
                        self.leg_index += 1
                        return
                    
                    #could be base route, or a loop that user doesn't want to try again.
                    self.charge(leg['close'] - self.time)                        #charge until stage close
                    
                #at this point stage must be closed. 
                if(is_last_leg):
                    self.printc('Completed the last loop, not enough time to complete another. Race done.')
                    self.done = True
                    return

                next_leg = self.legs[self.leg_index+1]
                if(self.try_loop and next_leg['type']=='loop'):
                    self.leg_index += 1
                    self.printc(f"Wait for next loop tomorrow: {next_leg['name']}")

                else:
                    while next_leg['type']!='base': #if don't want to try loop, pick the next base leg
                        self.leg_index += 1

                        if(not self.leg_index < len(self.legs)):
                            self.printc(f"Completed last base leg: {leg['name']}")
                            self.done = True
                            return

                        next_leg = self.legs[self.leg_index]
                    self.printc(f"Wait for next base leg tomorrow: {next_leg['name']}")
                
                self.charge(timedelta(hours=EVENING_CHARGE_HOURS))    #evening charging
                self.time = datetime(self.time.year, self.time.month, self.time.day+1, CHARGE_START_HOUR) #time skip to beginning of morning charging
                self.charge(timedelta(hours=MORNING_CHARGE_HOURS))    #morning charging
                # self.leg_index += 1
                return

            else:
                if(leg['type']=='base'):
                    self.printc('Did not make stagestop on time, considered trailered')        
                    self.done = True
                    self.miles_earned = 0
                    return
                else:

                    if(is_last_leg):
                        self.printc('Loop arrived after stage close, does not count. Race done.')
                        self.done = True
                        return

                    self.printc('Loop arrived after stage close, does not count. Moving onto next leg.')
                    self.charge(leg['close'] - self.time + timedelta(hours=EVENING_CHARGE_HOURS))      #charge until end of evening charging
                    self.time = next_leg['start'] - timedelta(MORNING_CHARGE_HOURS) #time skip to beginning of morning charging
                    self.charge(timedelta(hours=MORNING_CHARGE_HOURS))    #morning charging
                    self.leg_index += 1
                    return

    def get_next_leg(self):
        leg = self.legs[self.leg_index]
        if(leg['type'] == 'loop' and self.try_loop):
            return leg['name']
        if(not self.leg_index+1 < len(self.legs)):
            return None
        next_leg = self.legs[self.leg_index+1]
        if(next_leg['type'] == 'loop'):
            if(self.try_loop):
                return next_leg['name']
            else:
                if(self.leg_index+2 < len(self.legs)):
                    next_next_leg = self.legs[self.leg_index+2]
                    if(next_next_leg['type'] == 'base'):
                        return next_next_leg['name']
                else:
                    return None
        return next_leg['name']
        

    def get_motor_power(self, accel, speed, headwind, dist_change, alt_change):
        '''
        Motor power loss in W, positive meaning power is used
        '''
        P_drag = self.car_props['P_drag']
        P_fric = self.car_props['P_fric']
        P_accel = self.car_props['P_accel']
        mg = self.car_props['mass'] * 9.81

        if(dist_change > 1): #protect against zero division
            sinslope = (alt_change / dist_change)
        else:
            sinslope = 0

        #can probably be made into a matrix
        power_ff = speed * (P_drag*(speed + headwind)**2 + P_fric + mg*sinslope)      #power used to keep the avg speed
        power_acc = P_accel*accel*speed                                                                 #power used to accelerate (or decelerate)
        return power_ff + power_acc


    def step(self, action=None):
        '''Updates the simulation by 1 timestep, by default 5 seconds. Run this in a loop until it
        returns True, meaning the simulation has finished.'''

        if(self.load is not None):
            if(self.sim_step < len(self.load)):
                self.action = {
                    'target_mph': self.load['target_mph'][self.sim_step],
                    'acceleration': self.load['acceleration'][self.sim_step],
                    'deceleration': self.load['deceleration'][self.sim_step],
                    'try_loop': self.load['try_loop'][self.sim_step],
                }
            else:
                self.printc("Length of loaded inputs aren't long enough to complete race. Extending last avaliable input.")
                last = len(self.load) - 1
                self.action = {
                    'target_mph': self.load['target_mph'][last],
                    'acceleration': self.load['acceleration'][last],
                    'deceleration': self.load['deceleration'][last],
                    'try_loop': self.load['try_loop'][last],
                }


        if(self.pause):
            plt.pause(0.5)
            return False #not done

        self.sim_step += 1

        leg = self.legs[self.leg_index]
        self.current_leg = leg

        v_0 = self.speed
        dt = self.timestep
        d_0 = self.leg_progress     #meters completed of the current leg
        w = leg['headwind'](d_0, self.time.timestamp())
        if(isnan(w)): w = 0

        self.log['times'][-1].append(self.time.timestamp())
        self.log['dists'][-1].append(self.leg_progress)
        self.log['speeds'][-1].append(self.speed)
        self.log['target_mphs'][-1].append(self.get_target_mph())
        self.log['accelerations'][-1].append(self.get_acceleration())
        self.log['decelerations'][-1].append(self.get_deceleration())
        self.log['try_loops'][-1].append(self.get_try_loop())
        self.log['energies'][-1].append(self.energy)
        self.log['motor_powers'][-1].append(self.motor_power)
        self.log['array_powers'][-1].append(self.array_power)

        P_max_out = self.car_props['max_motor_output_power'] #max motor drive power (positive)
        P_max_in = self.car_props['max_motor_input_power'] #max regen power (negative)
        min_mph = self.car_props['min_mph']
        max_mph = self.car_props['max_mph']

        if action is not None:
            assert action['acceleration'] > 0, "Acceleration must be positive"
            assert action['deceleration'] < 0, "Deceleration must be negative"
            assert action['target_mph'] >= min_mph and action['target_mph'] <= max_mph, f"Target speed must be between {min_mph} mph and {max_mph} mph"

            self.action = action

            a_acc = float(action['acceleration'])
            a_dec = float(action['deceleration'])
            v_t = float(action['target_mph']) * mph2mpersec()
            self.try_loop = action['try_loop']
        else:
            a_acc = float(self.action['acceleration'])
            a_dec = float(self.action['deceleration'])
            v_t = float(self.action['target_mph']) * mph2mpersec()
            self.try_loop = self.action['try_loop']

        # SPEEDLIMIT
        if(d_0 >= self.next_limit_dist):     #update speed limit if passed next sign
            self.limit = leg['speedlimit'][1][self.next_limit_index]

            if(self.next_limit_index+1 < len(leg['speedlimit'][0])):
                self.next_limit_index += 1
                self.next_limit_dist = leg['speedlimit'][0][self.next_limit_index]
            else:
                self.next_limit_dist = float('inf')


        # STOPPING
        if(d_0 > self.next_stop_dist - 1000):       #check if within a reasonable stopping distance (1km)

            stopping_dist = -v_0*v_0 / (2*a_dec)    #calculate distance it would take to decel to 0 at current speed

            if(d_0 > self.next_stop_dist - stopping_dist):  #within distance to be able to decel to 0 at a constant decel
                a = a_dec
                v_avg = v_0/2.
                alt_change = leg['altitude'](self.next_stop_dist) - leg['altitude'](d_0)
                stopping_time = -v_0/a

                self.motor_power = self.get_motor_power(a, v_avg, w, stopping_dist, alt_change)
                self.energy -= self.motor_power * stopping_time

                self.array_power = leg['sun_flat'](d_0, self.time.timestamp()) * self.car_props['array_multiplier']
                if(not isnan(self.array_power)):
                    self.energy += self.array_power * stopping_time

                self.energy = min(self.energy, self.car_props['max_watthours']*3600)

                self.time += timedelta(seconds=stopping_time)
                self.leg_progress = self.next_stop_dist
                self.speed = 0

                if(self.next_stop_index+1 < len(leg['stop_dists'])):
                    self.next_stop_index += 1
                    self.next_stop_dist = leg['stop_dists'][self.next_stop_index]  #completed the stop
                else:
                    self.next_stop_dist = float('inf')

                return False


        # CALCULATE ACTUAL ACCELERATION
        d_f_est = d_0 + v_t*dt      #estimate dist at end of step for now by assuming actualspeed=targetspeed
        sinslope = (leg['altitude'](d_f_est) - leg['altitude'](d_0)) / (d_f_est - d_0)      #approximate slope

        P_drag = self.car_props['P_drag']
        P_fric = self.car_props['P_fric']
        P_accel = self.car_props['P_accel']
        mg = self.car_props['mass'] * 9.81

        v_t = min(v_t, self.limit) #apply speed limit to target speed
        v_error = v_t - v_0
        if(v_error > 0):        #need to speed up, a > 0
            if(np.abs(v_0) > 1): #avoid divide by 0
                motor_accel_limit = 1/P_accel * (P_max_out/v_0 - P_drag*(v_0-w)**2 - P_fric - mg*sinslope) #max achieveable accel for motor
                a = min(a_acc, motor_accel_limit)
            else:
                a = a_acc
        elif(v_error < 0):                   #need to slow down, a < 0
            if(np.abs(v_0) > 0.1):
                motor_decel_limit = 1/P_accel * (P_max_in/v_0 - P_drag*(v_0-w)**2 - P_fric - mg*sinslope) #max achieveable decel for motor (negative)
                brake_power = motor_decel_limit - a_dec             #power that mechanical brakes dissipate
                self.brake_energy += brake_power * dt
            a = a_dec           #assume accel can always reach the amount needed because of mechanical brakes
        else:
            a = 0

        if(np.abs(v_error) < np.abs(a * dt)): #adjust dt to not overshoot target speed
            dt = np.abs(v_error / a)

        # CALCULATE DISTANCE, SPEED, AND POWER NEEDED
        v_f = v_0 + a*dt                #get speed after accelerating
        v_avg = 0.5 * (v_0 + v_f)       #speed increases linearly so v_avg can be used in integration with no accuracy loss
        d_f = d_0 + v_avg * dt               #integrate velocity to get distance at end of step
        self.leg_progress = d_f
        self.speed = v_f

        alt_change = leg['altitude'](d_f) - leg['altitude'](d_0)

        self.motor_power = self.get_motor_power(a, v_avg, w, d_f-d_0, alt_change)
        self.energy -= self.motor_power * dt

        self.array_power = leg['sun_flat'](d_0, self.time.timestamp()) * self.car_props['array_multiplier']
        if(not isnan(self.array_power)):
            self.energy += self.array_power * dt

        self.energy = min(self.energy, self.car_props['max_watthours']*3600)
            
        self.time += timedelta(seconds=dt)

        if(self.energy <= 0):
            self.printc("No battery, ending simulation")
            self.end_race()
            return True
    
        # CHECK IF COMPLETED CURRENT LEG
        if(d_f >= leg['length']):
            self.printc(f"Completed leg: {leg['name']} at {self.time}")
            self.process_leg_finish() #will update leg and self.done if needed

            if(self.done):
                self.printc("Completed race, ending simulation.")
                self.end_race()
                return True

            self.current_leg = self.legs[self.leg_index]
            self.reset_leg()

            if(self.do_render):
                self.render_init()

        # CHECK IF END OF DAY
        if(self.time > datetime(self.time.year, self.time.month, self.time.day, DRIVE_STOP_HOUR)):

            if(self.time.day >= self.legs[-1]['close'].day):
                self.printc("Past close time of last leg, ending simulation.")
                self.end_race()
                return True

            self.charge(timedelta(hours=CHARGE_STOP_HOUR - DRIVE_STOP_HOUR))
            self.time = datetime(self.time.year, self.time.month, self.time.day+1, CHARGE_START_HOUR)
            self.charge(timedelta(hours=DRIVE_START_HOUR - CHARGE_START_HOUR))
            self.printc(f"End of day. Now {self.time.month}-{self.time.day}")


        if(self.do_render and self.sim_step % self.steps_per_render == 0):
            self.render()

        return False

    def end_race(self):
        if(self.save and self.load is None):
            df = pd.DataFrame.from_dict({
                'target_mph': flatten_list(self.log['target_mphs']),
                'acceleration': flatten_list(self.log['accelerations']),
                'deceleration': flatten_list(self.log['decelerations']),
                'try_loop': flatten_list(self.log['try_loops']),
                'is_keyboard': self.is_keyboard
            })
            miles = round(self.miles_earned)
            energy = round(self.energy/3600.)

            if(self.save_name is None or self.save_name == ''):
                filename = f"{self.save_name}{miles}mi_{energy}W"
            else:
                filename = self.save_name
            df.to_csv(f"{dir}/simulator/logs/{filename}.csv", index=False)

        self.done = True



    def render_init(self):
        self.transition = True
        plt.close('all')
        self.transition = False

        leg = self.current_leg

        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        self.fig = plt.figure(figsize=(15, 13 * screen_height/screen_width))

        ax_elev = plt.subplot2grid((3, 8), (0, 0), colspan=8)
        ax_speed = plt.subplot2grid((3, 8), (1, 0), colspan=7, rowspan=2)
        ax_power = plt.subplot2grid((3, 8), (1, 7), rowspan=1)
        ax_battery = plt.subplot2grid((3, 8), (2, 7), rowspan=1)

        #in meters
        self.distwindow_l = 0
        self.distwindow_r = miles2meters(self.dist_behind + self.dist_ahead)

        #elevation axes
        ax_elev.set_ylabel("Elevation (meters)")
        dists_leg = np.arange(0, leg['length'], step=30)
        elevs = self.current_leg['altitude'](dists_leg)
        self.min_elev = min(elevs)
        self.max_elev = max(elevs)
        ax_speed.set_ylim(0, self.max_elev*1.05)
        (self.ln_elev) = ax_elev.plot(dists_leg * meters2miles(), elevs, '-', label="elevation")
        (self.ln_distwindow_l,) = ax_elev.plot((meters2miles(self.distwindow_l), meters2miles(self.distwindow_l)), (self.min_elev, self.max_elev), 'y-')
        (self.ln_distwindow_r,) = ax_elev.plot((meters2miles(self.distwindow_r), meters2miles(self.distwindow_r)), (self.min_elev, self.max_elev), 'y-')
        (self.pt_elev,) = ax_elev.plot(0, leg['altitude'](0), 'ko', markersize=5)

        weather_step = round(leg['length'] / 100)
        self.weather_dists = np.arange(0, leg['length'], step=weather_step)
        n_dists = len(self.weather_dists)

        solars = leg['sun_flat'](self.weather_dists, self.time.timestamp())
        colors = interp_color(vals=solars, min_val=min(solars), max_val=max(solars), min_color=SUN_RED, max_color=SUN_YELLOW)
        self.pts_solar = ax_elev.scatter(self.weather_dists * meters2miles(), np.ones_like(self.weather_dists)*(self.min_elev + 1.05*(self.max_elev - self.min_elev)), c=colors, s=solars/10)
        ax_elev.text(-0.5, (self.min_elev + 1.05*(self.max_elev - self.min_elev)), "solar", ha='right', va='center')

        winds = self.current_leg['headwind'](self.weather_dists, self.time.timestamp())
        self.pts_wind = ax_elev.quiver(self.weather_dists * meters2miles(), np.ones_like(self.weather_dists)*(self.min_elev + 1*(self.max_elev - self.min_elev)), -winds, np.zeros(n_dists), headwidth=2, minlength=0, scale=200, scale_units='width')
        ax_elev.text(-0.5, (self.min_elev + 1.0*(self.max_elev - self.min_elev)), "wind", ha='right', va='center')


        ax_elev.legend(loc='lower left')


        #speed axes
        ax_speed.set_ylabel("Speed (mph)")
        ax_speed.set_xlabel("Distance (miles)")
        ax_speed.set_xlim(0, meters2miles(self.distwindow_r))
        ax_speed.set_ylim(0, self.car_props['max_mph']*1.1)

        limit_dist_pts, limit_pts = self.current_leg['speedlimit']

        limit_dist_pts, limit_pts = trim_to_range(self.limit_dist_pts, self.limit_pts, self.distwindow_l, self.distwindow_r)

        (self.ln_limit,) = ax_speed.plot(limit_dist_pts*meters2miles(), limit_pts*mpersec2mph(), label='Speed limit', c='gray')
        (self.ln_speed,) = ax_speed.plot(0, 0, label='Car speed', c='black')
        (self.pt_speed,) = ax_speed.plot(0, 0, 'ko', markersize=5)

        ax_speed.legend(loc='upper left')

        self.power_hist = 100
        self.battery_hist = 1000
        self.motor_powers_disp = np.full(self.power_hist*2, 0)
        self.array_powers_disp = np.full(self.power_hist, 0)
        self.battery_disp = np.full(self.battery_hist, self.energy/3600)

        #power axes
        ax_power.set_title("Array power (W)")
        ax_power.set_xlim(0, 3600)
        ax_power.set_ylim(-1000, 2000)
        ax_power.get_xaxis().set_visible(False)
        ax_power.plot([0, 3600], [0,0], 'k--')
        (self.ln_arraypower,) = ax_power.plot(0, 0, label='Array power', c='orange')
        (self.ln_motorpower,) = ax_power.plot(0, 0, label='Motor power', c='red')
        ax_power.legend(loc='lower right')

        #battery axes
        ax_battery.set_title("Battery Energy (Wh)")
        ax_battery.set_xlim(0, 3600)
        ax_battery.set_ylim(0, self.car_props['max_watthours']*1.05)
        ax_battery.get_xaxis().set_visible(False)
        (self.ln_battery,) = ax_battery.plot([0,3600], [self.energy/3600.,self.energy/3600.], label='Battery energy', c='green')

        #Text
        leg = self.current_leg
        closetime = leg['close'].strftime('%m/%d/%Y, %H:%M')
        ax_speed.set_title(f"{leg['name']}. Close time: {closetime}")
        self.tx_time = ax_speed.text(5, self.car_props['max_mph']*1.05, f"{self.time.strftime('%m/%d/%Y, %H:%M')}", fontsize=15, ha='center', va='top')
        self.tx_input = ax_speed.text(5, 0, "", fontsize=15, ha='center', va='bottom')


        plt.tight_layout()

        self.bm = BlitManager(self.fig, (
            self.pt_elev, self.ln_distwindow_l, self.ln_distwindow_r, self.pts_solar, self.pts_wind,
            self.ln_limit, self.ln_speed, self.pt_speed, self.tx_time, self.tx_input,
            self.ln_arraypower, self.ln_motorpower,
            self.ln_battery,
        ))

        #closing the first window deletes the second window
        def on_close(event):
            if not self.transition:
                self.printc("Window closed, ending simulation early.")
                sys.exit()
        self.fig.canvas.mpl_connect('close_event', on_close)

        def update_tx():
            if(self.tx_input is not None):
                if(self.pause):
                    pause_str = "Press [P] to unpause"
                else:
                    pause_str = "Press [P] to pause"
                
                speed_str = "[1-9] for simulation speed"

                if(self.load is not None):
                    action_str = f"Loaded input from file: {self.load_name}"
                else:
                    action_str = f"Target [Arrow keys]: {self.action['target_mph']}mph  \n Try loop [Enter]: {self.action['try_loop']}"
                next_leg_str = f"Upcoming leg: {self.get_next_leg()}"
                self.tx_input.set_text(f"{pause_str}\n{speed_str}\n{action_str}\n{next_leg_str}")


        def press(event):
            if(self.load is None):
                if(event.key == 'up'):
                    self.is_keyboard = True
                    self.action['target_mph'] = min(self.action['target_mph']+2, self.car_props['max_mph'])
                    update_tx()
                if(event.key == 'down'):
                    self.is_keyboard = True
                    self.action['target_mph'] = max(self.action['target_mph']-2, 5)
                    update_tx()
                if(event.key == 'enter'):
                    self.is_keyboard = True
                    self.action['try_loop'] = not self.action['try_loop']
                    self.try_loop = self.action['try_loop']
                    update_tx()
            if(event.key == 'p'):
                self.pause = not self.pause
                update_tx()
                self.bm.update()
            if(event.key.isdigit()):
                num = int(event.key)
                if(num >= 1 and num <= 9):
                    self.steps_per_render = num

            
        self.pause = True

        self.fig.canvas.mpl_connect('key_press_event', press)
        update_tx()

        plt.pause(.01) #wait a bit for things to be drawn and cached
        self.bm.update()

    def render(self):
        self.pt_elev.set_xdata(meters2miles(self.leg_progress))
        self.pt_elev.set_ydata(self.current_leg['altitude'](self.leg_progress))


        if(self.sim_step % 50 ==0):
            solars = self.current_leg['sun_flat'](self.weather_dists, self.time.timestamp())
            colors = interp_color(vals=solars, min_val=min(solars), max_val=max(solars), min_color=SUN_RED, max_color=SUN_YELLOW)
            self.pts_solar.set_facecolors(colors)
            self.pts_solar.set_sizes(solars/10)

            winds = self.current_leg['headwind'](self.weather_dists, self.time.timestamp())
            self.pts_wind.set_UVC(U=-winds, V=np.zeros_like(winds))

        if(self.leg_progress > miles2meters(self.dist_behind)):
            self.distwindow_l = self.leg_progress - miles2meters(self.dist_behind)
            self.distwindow_r = self.leg_progress + miles2meters(self.dist_ahead)
        
        dists_so_far = np.array(self.log['dists'][-1])
        speeds_so_far = np.array(self.log['speeds'][-1])

        speeds_dists_window, speeds_window = trim_to_range(dists_so_far, speeds_so_far, self.distwindow_l, self.distwindow_r)
        
        try:
            dist_shift = speeds_dists_window[0]
        except:
            dist_shift = 0

        self.ln_speed.set_xdata(meters2miles(speeds_dists_window-dist_shift))
        self.ln_speed.set_ydata(mpersec2mph(speeds_window))

        limit_dist_pts, limit_pts = trim_to_range(self.limit_dist_pts, self.limit_pts, self.distwindow_l - miles2meters(5), self.distwindow_r + miles2meters(5))
        self.ln_distwindow_l.set_xdata((meters2miles(self.distwindow_l), meters2miles(self.distwindow_l)))
        self.ln_distwindow_r.set_xdata((meters2miles(self.distwindow_r), meters2miles(self.distwindow_r)))

        self.ln_limit.set_xdata(meters2miles(limit_dist_pts - dist_shift))
        self.ln_limit.set_ydata(mpersec2mph(limit_pts))
        
        self.pt_speed.set_xdata(meters2miles(self.leg_progress-dist_shift))
        self.pt_speed.set_ydata(mpersec2mph(self.speed))

        self.motor_powers_disp = np.roll(self.motor_powers_disp, -1)
        self.motor_powers_disp[-1] = self.motor_power
        self.array_powers_disp = np.roll(self.array_powers_disp, -1)
        self.array_powers_disp[-1] = self.array_power
        self.battery_disp = np.roll(self.battery_disp, -1)
        self.battery_disp[-1] = self.energy/3600

        disp_step = 12
        if(self.sim_step % disp_step == 0):

            power_times = np.linspace(0, 3600, self.power_hist)

            motor_avg = moving_average(self.motor_powers_disp, self.power_hist)[-self.power_hist:]
            self.ln_motorpower.set_xdata(power_times)
            self.ln_motorpower.set_ydata(motor_avg)

            self.ln_arraypower.set_xdata(power_times)
            self.ln_arraypower.set_ydata(self.array_powers_disp)

            battery_times = np.linspace(0, 3600, self.battery_hist)
            self.ln_battery.set_xdata(battery_times)
            self.ln_battery.set_ydata(self.battery_disp)

            self.tx_time.set_text(self.time.strftime('%m/%d/%Y, %H:%M'))


        self.bm.update()
        plt.pause(self.pause_time)

    

    #setters and getters

    def set_target_mph(self, mph:float):
        '''Simulated car will try to reach this speed. Might not always reach this because of 
        motor limits, speed limits, stopsigns/stoplights, or no energy left.'''
        self.action['target_mph'] = mph

    def get_target_mph(self):
        return self.action['target_mph']
    
    def set_acceleration(self, acc:float):
        '''Simulated car will use this acceleration when current speed is less than the target
        speed. Measured in meters per second per second and should be positive. Typically 0.5 m/s^2'''
        self.action['acceleration'] = acc

    def get_acceleration(self):
        return self.action['acceleration']

    def set_deceleration(self, dec:float):
        '''Simulated car will use this deceleration when current speed is less than the target
        speed. Measured in meters per second per second and should be negative. Typically -0.5 m/s^2'''
        self.action['deceleration'] = dec

    def get_deceleration(self):
        return self.action['deceleration']

    def set_try_loop(self, try_loop:bool):
        self.action['try_loop'] = try_loop
        self.try_loop = try_loop

    def get_try_loop(self):
        return self.action['try_loop']

    def get_watthours(self):
        '''Battery energy remaining in watt-hours'''
        return self.energy / 3600.

    def get_miles_earned(self):
        '''Miles earned from finishing base legs or loops on time'''
        return self.miles_earned
    
    def get_legs_attempted(self):
        '''List of base legs or loops that were attempted'''
        return self.log['leg_names']

    def get_legs_completed(self):
        '''List of base legs or loops that were completed on time'''
        return self.legs_completed_names

    def get_time(self):
        '''Get the current time as a datetime object'''
        return self.time

    def get_leg_progress(self):
        '''Get the number of miles into the current leg'''
        return self.leg_progress * meters2miles()

    def get_average_mph(self):
        '''Get average mph since the start of the race'''
        speeds = flatten_list(self.log['speeds'])
        return np.mean(speeds) * mpersec2mph()

    def get_stddev_mph(self):
        '''Get average mph since the start of the race'''
        speeds = flatten_list(self.log['speeds'])
        return np.std(speeds) * mpersec2mph()

    def get_current_leg(self):
        '''Get the base or loop that the car is currently driving. Is a dict of a various route data.
        Can use this to get the weather forecast or slopes along the entire leg.'''
        return self.current_leg

    def get_all_legs(self):
        '''Get all the possible base legs or loops in the race'''
        return self.legs

    def get_log(self):
        '''Get the log dict, which contains the speed, distance, leg names, motor power, array power, etc. 
        at each time step.'''
        return self.log

    def get_slope(self, dist=None):
        '''Get the slope at a certain mile along the leg, in % grade (1% means 1m of elevation gain per 100m horizontal distance).
        If the parameter dist is left empty, default is current location.'''
        if(dist is None):
            dist = self.leg_progress
        else:
            dist = miles2meters(dist)
        slope = self.current_leg['slope'](dist)
        return slope

    def get_elevation(self, dist=None):
        '''Get the altitude at a certain mile along the leg, in meters.
        If the parameter dist is left empty, default is current location.'''
        if(dist is None):
            dist = self.leg_progress
        else:
            dist = miles2meters(dist)
        slope = self.current_leg['altitude'](dist)
        return slope

    def get_headwind(self, dist=None, time=None):
        '''Get the headwind in m/s at a certain mile and time along the leg.
        Input the date either as a datetime object or unix timestamp in the local timezone.
        If left empty, the default is the current location and current time.'''
        if(dist is None):
            dist = self.leg_progress
        else:
            dist = miles2meters(dist)        
        if(time is None):
            time = self.time
        if(isinstance(time, datetime)):
            time = time.timestamp()
        headwind = self.current_leg['headwind'](self.leg_progress, time)
        return headwind

    def get_solar_flat(self, dist=None, time=None):
        '''Get the solar irradiance in W/m^2 at a certain mile and time along the leg with a horizontal array.
        This irradiance is used when the car is driving.
        Input the date either as a datetime object or unix timestamp in the local timezone.
        If left empty, the default is the current location and current time.'''
        if(dist is None):
            dist = self.leg_progress
        else:
            dist = miles2meters(dist)
        if(time is None):
            time = self.time
        if(isinstance(time, datetime)):
            time = time.timestamp()
        solar_flat = self.current_leg['sun_flat'](self.leg_progress, time)
        return solar_flat

    def get_solar_tilt(self, dist=None, time=None):
        '''Get the solar irradiance in W/m^2 at a certain mile and time along the leg with an array tilted at the optimal angle.
        This irradiance is used when the car is stopped to charge.
        Input the date either as a datetime object or unix timestamp in the local timezone.
        If left empty, the default is the current location and current time.'''
        if(dist is None):
            dist = self.leg_progress
        else:
            dist = miles2meters(dist)
        if(time is None):
            time = self.time
        if(isinstance(time, datetime)):
            time = time.timestamp()
        solar_tilt = self.current_leg['sun_tilt'](self.leg_progress, time)
        return solar_tilt

    def get_leg_index(self):
        '''Get the index of the leg the car is currently driving'''
        return self.leg_index

    def get_car_props(self):
        '''Get the dict of car properties. See the .json files in the cars/ folder for the information offered.'''
        return self.car_props