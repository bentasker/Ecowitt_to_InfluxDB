# Ecowitt Listener

Small docker image to receive writes from weather stations using Ecowitt protocol and write the data into an upstream InfluxDB instance (OSS, Enterprise or Cloud).

----

### Examples

Writing into [InfluxCloud](https://cloud2.influxdata.com)

    docker run -d \
    -p 8090:8090 \
    -e INFLUX_URL="https://eu-central-1-1.aws.cloud2.influxdata.com" \
    -e INFLUX_ORG="myaddress@example.invalid" \
    -e INLUX_TOKEN="====" \
    -e INFLUX_BUCKET="weather" \
    bentasker12/ecowitt_listener

Writing into an unauthenticated Influx 1.x instance

    docker run -d \
    -p 8090:8090 \
    -e INFLUX_URL="http://myinfluxinstance:8086" \
    -e INFLUX_BUCKET="weather" \
    bentasker12/ecowitt_listener

Writing into an authenticated Influx 1.x instance

    docker run -d \
    -p 8090:8090 \
    -e INFLUX_URL="http://myinfluxinstance:8086" \
    -e INFLUX_BUCKET="weather" \
    -e INLUX_TOKEN="ben:secretpassword" \
    bentasker12/ecowitt_listener
    
Writing into an OSS 2.x instance

    docker run -d \
    -p 8090:8090 \
    -e INFLUX_URL="http://myinfluxinstance:8086" \
    -e INFLUX_ORG="myaddress@example.invalid" \
    -e INLUX_TOKEN="====" \
    -e INFLUX_BUCKET="weather" \
    bentasker12/ecowitt_listener

----
    
### Configuration Options

The default configuration is set to suit me, so may not suit you.

The following environment variables can be exported to control behaviour


- `IGNORE`: Which fields in the input should be skipped (default: "PASSKEY,stationtype,dateutc,freq")
- `TAGS`: Which fields in the input should be converted to tags (default: "model")
- `MEASUREMENT`: Name of the measurement to write  into (default: "weather")
- `DEBUG`: Set non-empty to enable debugging
- `RAIN_MM`: Convert rain from Inches to MM (Default: "yes")
- `PRESSURE_HPA`: Convert pressure readings to HPA (Default: "yes")
- `TEMP_C`: Convert temperature readings to Centigrade (Default: "yes")
- `SPEED_KPH`: Convert speed to KPH (Default: "no")

----

### Fields

The name of some fields seems to differ between device.

* `wh[num]bat` (e.g. `wh65batt`) - battery status ([apparently](https://www.weather-watch.com/smf/index.php?topic=70002.0), 0 = OK, 1 = low)
* `totalrainin`/`totalrainmm`: Total rain recorded in inches/mm
* `yearlyrainin`/`yearlyrainmm`: Total rain recorded in inches/mm this year
* `monthlyrainin`/`monthlyrainmm`: Total rain recorded in inches/mm this month
* `weeklyrainin`/`weeklyrainmm`: Total rain recorded in inches/mm this week
* `dailyrainin`/`dailyrainmm`: Total rain recorded in inches/mm today
* `hourlyrainin`/`hourlyrainmm`: Total rain recorded in inches/mm in this hour
* `eventrainin`/`eventrainmm`: Total rain recorded in inches/mm so far in this shower
* `rainratein`/`rainratemm`: Current rainfall rate in inches/mm
* `uv`: UV index
* `solarradiation`: Solar radiation (w/m2)
* `maxdailygust` / `maxdailygustkph`: Maximum wind gust speed today (MPH/KPH)
* `windgustmph` / `windgustkph`: Gust speed (MPH/KPH)
* `windspeedmph` / `windspeedkph`: Wind speed (MPH/KPH)
* `winddir`: Wind direction (degrees)
* `humidity`: Outside humidity (%)
* `tempf` / `tempc`: Outside temperature (F/C)
* `baromrelin` / `baromrelhpa`: Relative pressure (inches/hpa)
* `baromabsin` / `baromabshpa`: Absolute pressure (inches/hpa)
* `humidityin`: Inside humidity (%)
* `tempinf` / `tempinc`: Inside temperature (F/C)

----

### Tags

Tags added are

* `model`: The model number submitted by the downstream
* `submitted_by`: The IP address of the unit writing stats in

Fields can be converted to tags by including their name in the environment variable `TAGS`.

----

### License

Copyright (c) 2022 Ben Tasker.

Released under [BSD-3-Clause](LICENSE)
