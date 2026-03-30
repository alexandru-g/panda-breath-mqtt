FROM python:3.13-alpine

WORKDIR /app

RUN pip install --no-cache-dir \
    "websockets>=13.0" \
    "aiomqtt>=2.0" \
    "pydantic>=2.0" \
    "pydantic-settings>=2.0"

COPY panda_breath_mqtt/ /app/panda_breath_mqtt/
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/run.sh"]
