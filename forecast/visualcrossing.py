from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
try:
    from .util import *     #when this file is being imported elsewhere
except:
    from util import *      #when this file is being run directly

key = ''
with open(dir + '/key.txt', 'r') as keyfile:
    split = keyfile.read().split('\n')
    key = split[2]  # visual crossing key (free version allows 1000 records a day)

def get_hour(latitude, longitude, time: datetime, doPrint=False, fakeRequest=False):
    '''
    Gets solar, cloud, wind, precip, and temp from VisualCrossing for a particular hour, using 1 record cost.
    Set fakeRequest to True to not make a request and return a dict of all 0, useful for testing how many records 
    something might cost.
    '''
    forecast_sec = round(time.timestamp())
    requests_text = ('https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline' 
        + '/' + str(latitude) + ',' + str(longitude)
        + '/' + str(forecast_sec)
        + '?key=' + key
        + '&include=current'
        + '&elements=datetimeEpoch,solarradiation,cloudcover,windspeed,winddir,precip,temp'
        + '&unitGroup=metric'
    )
    if(doPrint): print(requests_text)

    if not fakeRequest:
        return requests.get(requests_text).json()['currentConditions']
    else:
        return {
            'datetimeEpoch': np.random.randint(0, 10),
            'solarradiation': np.random.random(),
            'cloudcover': np.random.random(),
            'windspeed': np.random.random(),
            'winddir': np.random.random(),
            'precip': np.random.random(),
            'temp': np.random.random(),
        }


def get_range(latitude, longitude, start_day: datetime, start_hour=7, end_hour=20, num_days=1, save=None, doPrint=False, fakeRequest=False):
    '''
    Gets solar, cloud, wind, precip, and temp from VisualCrossing in the time range, for multiple days. 
    The number of record costs used is the total number of forecasted hours. Optionally save as csv.
    \n solarradiation in W/m^2
    \n cloudcover in percent
    \n windspeed in km/hr
    \n winddir in degrees
    \n precip in mm
    \n temp in degrees Celcius
    '''

    weather_dict = {
        'datetimeEpoch': [],
        'solarradiation': [],
        'cloudcover': [],
        'windspeed': [],
        'winddir': [],
        'precip': [],
        'temp': [],
    }

    records_used = 0

    for day_index in range(num_days):
        forecast_day = datetime(start_day.year, start_day.month, start_day.day) + timedelta(days=day_index)

        for hour in range(start_hour, end_hour + 1):

            conditions = get_hour(latitude, longitude, forecast_day + timedelta(hours=hour), doPrint=doPrint, fakeRequest=fakeRequest)
            records_used += 1

            for key in weather_dict:
                weather_dict[key].append(conditions[key])

    weather_dict['date'] = [datetime.fromtimestamp(timestamp) for timestamp in weather_dict['datetimeEpoch']]

    weather_df = pd.DataFrame.from_dict(weather_dict)

    if save is not None:
        weather_df.to_csv(save, index=False)
            
    return weather_df, records_used


print(get_hour(39, -95, datetime.now()))