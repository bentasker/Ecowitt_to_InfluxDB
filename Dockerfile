FROM python

ENV IGNORE = "PASSKEY,stationtype,dateutc,freq"
ENV TAGS "model"
ENV MEASUREMENT "weather"
ENV DEBUG
ENV INFLUX_BUCKET "testing_db"
ENV INFLUX_ORG ""
ENV INFLUX_TOKEN ""
ENV INFLUX_URL "http://192.168.3.84:8086"

RUN pip install flask influxdb_client

COPY app /app

CMD "/app/ecowitt.py"
