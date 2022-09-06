import requests
from datetime import datetime
from timezonefinder import TimezoneFinder

tzfinder = TimezoneFinder()

def get_wind_solar(latitude, longitude, start:datetime, stop:datetime):

    vars = [
        'shortwave_radiation',      #total sun for horizontal array 
        'direct_normal_irradiance', #used to calculate total sun for tilted array
        'diffuse_radiation',        #used to calculate total sun for tilited array (add to direct)
        'windspeed_10m',
        'winddirection_10m',
    ]

    #get timezone at coordinate so timestamps make sense
    timezone = tzfinder.timezone_at(lat=latitude, lng=longitude)

    timestamps_trunc = []
    weather_vals = {}
    for var in vars:

        response = requests.request(
            method = "GET", 
            url = "https://api.open-meteo.com/v1/forecast?", 
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": var,
                "windspeed_unit": "ms",
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": stop.strftime("%Y-%m-%d"),
                "timeformat": "unixtime",
                "timezone": timezone
            }
        ).json()
        
        try:
            values = response['hourly'][var]
            timestamps = response['hourly']['time']
        except Exception as e:
            print(f"Error: {e} \n {response}")

        if(values[0] == None): values[0] = 0

        while values and values is None:    #remove trailing Nones
            values[var].pop()

        if(len(timestamps_trunc) == 0):
            timestamps_trunc = timestamps[:len(values)] #truncate timestamps to match values
        weather_vals[var] = values

    if('direct_normal_irradiance' in weather_vals and 'diffuse_radiation' in weather_vals):
        weather_vals['sun_flat'] = weather_vals['shortwave_radiation']
        weather_vals['sun_tilt'] = [sum(x) for x in zip(weather_vals['direct_normal_irradiance'], weather_vals['diffuse_radiation'])]

        del weather_vals['shortwave_radiation']
        del weather_vals['direct_normal_irradiance']
        del weather_vals['diffuse_radiation']
        
    return timestamps_trunc, weather_vals

# print(get_wind_solar(39, -95, datetime(2022, 7, 9), datetime(2022, 7, 10)))