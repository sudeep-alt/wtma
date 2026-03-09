# WTMA: Who touched my app?
WTMA is an ASGI middleware purposed to log every IP on your web app with detailed info.
**Version:** 0.1.0

## Features
- Geolocation logging: Log every IP with their geolocation data, such as country, continent. region and city.
- Proxy checking: Verify whether IPs were associated with proxies.
- Hosting checking: Verify whether IPs were associated with hosting and datacenters.
- Last visit: View the dynamic and exact time when an IP hit your app.
- Multiple formats: Log data in either JSON or TOML format.
- Console logging: View brief IP info in the console as well.
- Framework support: Supports all ASGI frameworks ([FastAPI](https://fastapi.tiangolo.com/), [Starlette](https://starlette.dev/) etc.)

## Quickstart
### Install the `wtma` python package
```commandline
pip install wtma
```
### Implement it to your app
**FastAPI exmaple:**
```python
from fastapi import FastAPI
from wtma import WTMA

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Hello, world!"
    }

# Wrap the app at the end
app = WTMA(
    app,
    log_path="log.json",
    file_format="JSON",
    log_to_console=True
)
```

Also, here's the signature of the constructor method:
```python
    def __init__(self, app, log_path: str, file_format:Literal["JSON", "TOML"]="JSON", log_to_console:bool=True):
```

> [!NOTE]
It's recommended to wrap the app with `WTMA` class at the end instead of using `add_middleware` because [Starlette](https://starlette.dev/),
which [FastAPI](https://fastapi.tiangolo.com/) is built on top of, suppresses exceptions raised in middleware's initialization, making it difficult to
debug.

## Log samples
### JSON
```json
{
  "1.1.1.1": {
    "country": "Australia",
    "continent": "Oceania",
    "city": "South Brisbane",
    "region": "QLD",
    "is_proxy": false,
    "is_hosting": true,
    "is_mobile": false,
    "reverseDNS": "one.one.one.one",
    "last_seen": "2026-03-08 15:54:05.067613+00:00"
  }
}
```

### TOML
```toml
["1.1.1.1"]
country = "Australia"
continent = "Oceania"
city = "South Brisbane"
region = "QLD"
is_proxy = false
is_hosting = true
is_mobile = false
reverseDNS = "one.one.one.one"
last_seen = "2026-03-08 15:54:05.067613+00:00"
```

## Data source
WTMA uses [ip-api.com](https://ip-api.com/) as its data source. The data returned may contain errors or be inaccurate.

If you found this project useful, please consider giving it a star!
