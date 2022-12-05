FROM python:3.9.6-alpine3.14

RUN  pip3 install --no-cache-dir prometheus_client requests

COPY ./metrics.py /metrics.py

ENTRYPOINT ["python"]

CMD ["/metrics.py"]
