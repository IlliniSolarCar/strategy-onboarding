
from bisect import bisect_left
from datetime import datetime
import os
import numpy as np
from numpy import sin, cos, pi
import math
import pandas as pd
from matplotlib.colors import Colormap, Normalize

dir = os.path.dirname(__file__)

to_dates = np.vectorize(datetime.fromtimestamp)

def meters2miles(meters=1):
    return meters * 0.0006214

def miles2meters(miles=1):
    return miles * 1609.34

def feet2meters(feet=1):
    return feet * 0.3048

def meters2feet(meters=1):
    return meters * 3.28

def mph2mpersec(mph=1):
    return mph * 0.44704

def mpersec2mph(mpersec=1):
    return mpersec * 2.23694

def latlong_dist(origin, destination):
    '''haversine formula for getting earth surface distance (km) between 2 lat/long pairs'''
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def solar_altitude_angle(time_obj:datetime, latitude, longitude, tz_offset):
    day_of_year = time_obj.tm_yday
    Latitude = latitude * (2 * np.pi / 360)

    local_solar_time_meridian = 15*tz_offset

    B = (day_of_year - 81)*360./365. * (2 * np.pi / 360.)
    E = 9.87*sin(2*B) - 7.53*cos(B) - 1.58*sin(B)
    time_correction_factor = 4 * \
        (longitude - local_solar_time_meridian) + E  # in minutes
    local_solar_time = time_obj.tm_hour + \
        (time_obj.tm_min+time_correction_factor)/60.

    Solar_Hour_Angle = (12 - local_solar_time) * 15 * (2 * np.pi / 360)
    Solar_Declination = (-23.45 * cos((day_of_year+10)
                                      * 2*pi/365)) * (2 * np.pi / 360)

    Solar_Altitude_Angle = np.arcsin(cos(Latitude) * cos(Solar_Declination) * cos(
        Solar_Hour_Angle) + sin(Latitude) * sin(Solar_Declination))

    return Solar_Altitude_Angle

def print_dict(d, indent=0):
   for key, value in d.items():
        print('\t' * indent + str(key) + ':')
        if isinstance(value, dict):
            print_dict(value, indent+1)
        else:
            print('\t' * (indent+1) + repr(value))

def ffill(x_0:list, y_0:list, epsilon=1e-6):
    '''
    Forward fill: Add points to a pair of lists so that the y value keeps constant until changed, creating steps instead of allowing graphs to interpolate
    '''
    x = np.array(x_0).tolist()
    y = np.array(y_0).tolist()
    assert len(x) == len(y)
    i = 1
    while i < len(x):
        x.insert(i, x[i]-epsilon)
        y.insert(i, y[i-1])
        i += 2
    return np.array(x), np.array(y)

def trim_to_range(x, y, left, right):
    '''trims x and y arrays so left < x < right'''
    x = np.array(x)
    y = np.array(y)
    l = bisect_left(x, left)
    r = bisect_left(x, right)
    x_trim = x[l:r]
    y_trim = y[l:r]
    return x_trim, y_trim

SUN_YELLOW = np.array([255, 224, 0]) / 255
NIGHT_GRAY = np.array([0, 0, 0]) / 255
def interp_color(vals, min_val, max_val, min_color, max_color):
    '''serves as a colormap between 2 colors given a list/array of scalars'''
    vals = np.array(vals)
    diff = np.array(max_color) - np.array(min_color)
    vals_norm = (vals - min_val)/(max_val - min_val)
    return np.outer(vals_norm, diff) + min_color

# sun_cmap = Colormap('inferno')
# def solar_color(solars):
#     solars = Normalize(min(solars), max(solars))(solars)
#     # solars = np.array(solars)
#     return sun_cmap(solars)




#testing
if __name__ == "__main__":
    x = (1, 1, 0)
    y = (2, 0, 1)
    c = interp_color([1, 2, 3, 4, 5 , 6], 1, 6, x, y)
    print(c)