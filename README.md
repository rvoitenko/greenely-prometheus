# greenely-prometheus

PoC for grab metrics from Greenely API and provide them as Prometheus metrics.

## Usage
```shell
docker run -it --rm  -p 9101:9101 --env=GR_EMAIL=YOUR_EMAIL --env=GR_PASSWORD=YOUR_PASS rvoitenko/greenely-prometheus:latest
```


exported metrics:

```shell
# TYPE greenely_spot_price gauge
greenely_spot_price 5.71
# HELP greenely_el_usage last daily usage, kWh
# TYPE greenely_el_usage gauge
greenely_last_day_usage 38.2
# HELP greenely_total_usage total usage from month beginning, kWh
# TYPE greenely_total_usage gauge
greenely_total_usage 101.7
```