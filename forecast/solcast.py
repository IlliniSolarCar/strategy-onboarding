import datetime
from datetime import timezone, timedelta, datetime
import requests
import os

dir = os.path.dirname(__file__)
with open(dir + '/key.txt', 'r') as keyfile:
    split = keyfile.read().split('\n')
    key = split[1]  # solcast key is the second one

def format_time_from_solcast(solcast_time, tz_offset):
    #Solcast gives time in an annoying format, so this method fixes it
    first_period = solcast_time.find('.')
    formatted_time_str = solcast_time[:first_period]
    formatted_time_str = formatted_time_str.replace('T', '-')
    old_time_obj = datetime.fromisoformat(formatted_time_str)
    #old_time_obj.tzinfo=timezone.utc
    current_timezone_obj = old_time_obj.replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=tz_offset)))
    return current_timezone_obj

def get_ghis(latitude, longitude, hours=24): #@todo actually read rulebook to say tilt
    requests_text = ('https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude=' 
        + str(latitude) 
        + '&longitude=' + str(longitude) 
        + '&format=json&api_key=' + key 
        + '&hours=' + str(hours)
        + '&output_parameters=' + 'air_temp,dni,dhi,ghi,wind_direction_10m,wind_speed_10m'
    )

    # irr_api_call = requests.get(requests_text)

    print('request: ' + requests_text)

    # if (irr_api_call.status_code == 200):
    #     ghis = []
    #     irr_response = irr_api_call.json()
        
    #     for i in range(0, len(irr_response['forecasts'])):
    #         ghis.append(irr_response['forecasts'][i]['ghi'])
    #     return ghis, irr_response

    # else:
    #     print("error: can't read api call. returning None")
    #     return None

print(get_ghis(39, -95))