FROM python

LABEL org.opencontainers.image.authors="github@bentasker.co.uk"
LABEL org.opencontainers.image.source="https://github.com/bentasker/Ecowitt_to_InfluxDB"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"


ENV IGNORE "PASSKEY,stationtype,dateutc,freq"
ENV TAGS "model"
ENV MEASUREMENT "weather"
ENV DEBUG ""
ENV INFLUX_BUCKET "testing_db"
ENV INFLUX_ORG ""
ENV INFLUX_TOKEN ""
ENV INFLUX_URL "http://192.168.3.84:8086"

# Set to "no" to disable conversion
ENV RAIN_MM "yes"
ENV PRESSURE_HPA "yes"
ENV TEMP_C "yes"

# Sorry everyone, I'm British
ENV SPEED_KPH "no"

ENV MET_OFFICE_WOW_ENABLED "no"
ENV MET_OFFICE_SITE_ID ""
ENV MET_OFFICE_SITE_PIN ""
ENV MET_OFFICE_SOFTWARE_IDENT "github.com/bentasker/Ecowitt_to_InfluxDB"
ENV MET_OFFICE_UPDATE_INTERVAL "5"
ENV MET_OFFICE_URL "https://wow.metoffice.gov.uk/automaticreading"


RUN pip install flask influxdb_client requests

COPY app /app

CMD "/app/ecowitt.py"
