#!/usr/bin/env python3
#
# Receive Ecowitt format payloads and write them out to InfluxDB
#
#
# Copyright (c) 2022 B Tasker
#
# Released under BSD-3-Clause License, see LICENSE in the root of the project repo
#

import influxdb_client
import os
import requests
import sys

from datetime import datetime
from flask import Flask, request
from influxdb_client.client.write_api import SYNCHRONOUS

app = Flask(__name__)

# Todo - take these from the environment
IGNORE = os.getenv("IGNORE", "PASSKEY,stationtype,dateutc,freq").split(",")
TAGS = os.getenv("TAGS", "model").split(",")
MEASUREMENT = os.getenv("MEASUREMENT", "weather")

INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "testing_db")
INFLUX_ORG = os.getenv("INFLUX_ORG", "")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
# Store the URL of your InfluxDB instance
INFLUX_URL = os.getenv("INFLUX_URL", "http://192.168.3.84:8086")
DEBUG = os.getenv("DEBUG", False)

# Do we convert from Freedom units
RAIN_MM = (os.getenv("RAIN_MM", "yes") == "yes")
PRESSURE_HPA  = (os.getenv("PRESSURE_HPA", "yes") == "yes")
TEMP_C = (os.getenv("TEMP_C", "yes") == "yes")
SPEED_KPH = (os.getenv("SPEED_KPH", "yes") == "yes")


# Should we pass onward to Met Office WOW?
MET_OFFICE_WOW_ENABLED = (os.getenv("MET_OFFICE_WOW_ENABLED", "yes") == "yes")
MET_OFFICE_SITE_ID = os.getenv("MET_OFFICE_SITE_ID", False)
MET_OFFICE_SITE_PIN = os.getenv("MET_OFFICE_SITE_PIN", False)
MET_OFFICE_SOFTWARE_IDENT = os.getenv("MET_OFFICE_SOFTWARE_IDENT", "github.com/bentasker/Ecowitt_to_InfluxDB")
MET_OFFICE_UPDATE_INTERVAL = int(os.getenv("MET_OFFICE_UPDATE_INTERVAL", 5))
MET_OFFICE_URL = os.getenv("MET_OFFICE_URL", "https://wow.metoffice.gov.uk/automaticreading")


@app.route('/')
def version():
    return "Ecowitt listener\n"


@app.route('/data/report/', methods=['POST'])
def receiveEcoWitt():
    ''' Receive a post in Ecowitt protocol format and process it 
    
    '''

    '''
    From packet capture

    POST /data/report/ HTTP/1.1
    HOST: weatherreport.bentasker.co.uk
    Connection: Close
    Content-Type: application/x-www-form-urlencoded
    Content-Length:182 

    PASSKEY=02EB4812BE8FE29E25936DCC71B81862&stationtype=GW1100A_V2.0.4&dateutc=2022-03-23+17:47:28&tempinf=77.5&humidityin=38&baromrelin=30.428&baromabsin=30.428&freq=868M&model=GW1100AHTTP/1.1 200 OK
    Server: nginx/1.14.2
    Date: Wed, 23 Mar 2022 17:47:28 GMT
    Content-Type: application/octet-stream
    Content-Length: 0
    Connection: close
    '''        
    
    
    remote_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)   
    
    fieldset = {}
    tagset = {"submitted_by" : remote_ip}
    
    # Iterate over each pair in the post body
    data = request.form
    for key in data:
        if DEBUG:
            print(f"{key}: {data[key]}\n")

        if key in IGNORE:
            continue

        #if key.endswith("batt"):
        #    # Not clear what it is, always seems to read 0
        #    continue

        # The dict isn't actually a dict, but an immutable dict like object
        # copy the value into a var so we can modify it as needed
        val = data[key]
        if key in TAGS:
            tagset[key] = val
            continue
        
        val = float(val)
        
        if TEMP_C and key.startswith("temp") and key.endswith("f"):
            val = convertFtoC(val)
            key = key[:-1] + 'c'

        if PRESSURE_HPA and key.startswith("barom") and key.endswith("in"):
            # Convert inches to hPa
            val = val * 33.6585
            key = key[:-2] + 'hpa'

        if RAIN_MM and (key.endswith("rainin") or key == "rainratein"):
            # Convert inches to mm
            val = val * 25.4
            key = key[:-2] + 'mm'

        if SPEED_KPH and key.endswith('mph'):
            speed = val * 1.60934
            key = key[:-3] + 'kph'

        if SPEED_KPH and key == "maxdailygust":
            speed = val * 1.60934
            key += "kph"
            

        # Push into the fields dict
        fieldset[key] = val
        
    # turn it into LP
    pt = build_point(tagset, fieldset)
    write_lp(pt)
    
    if DEBUG:
        print(pt)
        
    # Pass on to optionally push out to the Met's service
    write_wow_data(data, fieldset)
    return ''


def build_wow_params(pd, fieldset):
    ''' Build the params that'll be sent onto the Met Office - these will be turned into a QS later
    
    Not going to lie, I wish I'd looked at their docs much earlier, turns out
    Ecowitt's protocol is basically identical to it.
    
    https://wow.metoffice.gov.uk/support/dataformats#automatic
    '''
    params = {
        'siteid' : MET_OFFICE_SITE_ID,
        'siteAuthenticationKey' : MET_OFFICE_SITE_PIN,
        'softwaretype' : MET_OFFICE_SOFTWARE_IDENT,
        }
    
    if "dateutc" in pd:
        params['dateutc'] = pd['dateutc']
    else:
        params['dateutc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    if "baromrelin" in pd:
        params['baromin'] = pd['baromrelin']

    # Some of the fields are identical between protocols
    direct_translations = ["dailyrainin", "humidity", "tempf", "winddir", "windspeedmph", "windgustmph"]
    for field in direct_translations:
        if field in pd:
            params[field] = pd[field]
    
    return params

def write_wow_data(pd, fieldset):
    ''' If writing into the MET Office's WOW is enabled, build the request
    '''
    
    if not MET_OFFICE_WOW_ENABLED:
        return
    
    
    if (not int(datetime.utcnow().strftime('%M')) % MET_OFFICE_UPDATE_INTERVAL):
        # Skip this iteration
        return
    
    # Otherwise, build the query string
    params = build_wow_params(pd, fieldset)
    
    try:
        r = requests.get(MET_OFFICE_URL, params=params)
        print("MET says {}".format(r.status_code))
    except:
        print("Warn: failed to submit to Met office")
    
    
    

def write_lp(pt):
    ''' Set up to send into Influx
    '''
    with influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(INFLUX_BUCKET, INFLUX_ORG, pt)
        
    
    
def build_point(tagset, fieldset):
    ''' Build some line protocol
    '''
    
    pt = influxdb_client.Point(MEASUREMENT)
    
    for tag in tagset:
        pt.tag(tag, tagset[tag])
        
    for field in fieldset:
        pt.field(field, fieldset[field])
        
    return pt


def convertFtoC(f):
    ''' Convert Farenheit to Celsius
    '''
    return (float(f) - 32) * 5 /9
    


if __name__ == "__main__":
    if MET_OFFICE_WOW_ENABLED and (not MET_OFFICE_SITE_ID or not MET_OFFICE_SITE_PIN):
        print("ERROR: You've enabled WOW integration by not provided MET_OFFICE_SITE_ID or MET_OFFICE_SITE_PIN")
        sys.exit(1)
        
    app.run(host="0.0.0.0", port=8090, debug=DEBUG)
