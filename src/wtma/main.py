import tomllib
from pathlib import Path
from beartype import beartype
from typing import Literal
import httpx
import json
from datetime import datetime, UTC
import logging
import tomli_w

logging.basicConfig(level=logging.INFO, format='%(message)s')
# Disable HTTPX logging
logging.getLogger("httpx").setLevel(logging.WARNING)


class WTMA:
    @beartype
    def __init__(self, app, log_path: str, file_format:Literal["JSON", "TOML"]="JSON", log_to_console:bool=True):
        self.app = app
        self.log_path = log_path
        self.file_format = file_format.upper()
        self.log_to_console = log_to_console

    async def __call__(self, scope, receive, send):

        ip = scope["client"][0]
        data = {}

        # JSON FORMAT HANDLING
        if self.file_format == "JSON":
            # Check if the JSON log file already exists and already stores the data for the IP, if so, only update the time
            if Path(self.log_path).exists() and Path(self.log_path).is_file():
                with open(self.log_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.decoder.JSONDecodeError:
                        if f.read():
                            raise Exception(f"The currently existing file {self.log_path} does not contain valid JSON")

                # Status code errors (!= 200) need to be retried since they're caused by stuff like rate limits (429),
                # but errors caused by 'status' key not being 'success' don't need to be tried because
                # they're caused by things like private, reserved IP range and invalid query, so we are verifying
                # either the message key is absent (all necessary data gathered) or exists but doesn't start with
                # "Status code: " meaning not a status code error so it doesn't need to be retried hence we can safely
                # retain the already present data and only update the last_seen key

                if (data.get(ip) and not data.get(ip).get("detail")) or (data.get(ip) and data.get(ip).get("detail") and not data.get(ip).get("detail").startswith("Status code: ")):
                    # Update the last seen only, use ISO 8601 time format
                    data[ip]["last_seen"] = str(datetime.now(UTC))

                    with open(self.log_path, "w") as f:
                        f.write(json.dumps(data, indent=4))

                    # Also log even when data is already stored if logging enabled
                    # Check if message key is absent which implies the request stored in logs has all necessary
                    # data, so well use that for logging
                    if self.log_to_console and not data.get(ip).get("detail"):
                        stored_data = data[ip]
                        logging.info(f"""
                            IP: {ip}
                            Country: {stored_data["country"]}
                            Continent: {stored_data["continent"]}
                            Proxy: {stored_data["is_proxy"]}
                            """)

                    await self.app(scope, receive, send)
                    return


            # If absent, send request
            async with httpx.AsyncClient() as client:
                ip = scope["client"][0]
                response = await client.get(
                    f"http://ip-api.com/json/{ip}?fields=status,country,continent,city,regionName,proxy,hosting,mobile,reverse")
                response_json = response.json()

            # Immediately log to console if console logging is enabled
            if self.log_to_console:
                if response_json["status"] != "success" or response.status_code != 200:
                    logging.warning(
                        f"IP lookup for \'{ip}\' failed, status code: {response.status_code}" if response.status_code != 200 else f"IP lookup for \'{ip}\' failed, \'status\' key wasn't \'success\'")
                else:
                    logging.info(f"""
                    IP: {ip}
                    Country: {response_json["country"]}
                    Continent: {response_json["continent"]}
                    Proxy: {response_json["proxy"]}
                    """)

            # Log to file and stuff
            if response_json["status"] != "success" or response.status_code != 200:
                data[ip] = {
                    "detail": "IP lookup failed",
                    "reason": "\'status\' key wasn't \'success\'" if response_json["status"] != "success" else f"Status code: {response.status_code}",
                    "last_seen": str(datetime.now(UTC))
                }
            else:
                data[ip] = {
                    "country": response_json["country"],
                    "continent": response_json["continent"],
                    "city": response_json["city"],
                    "region": response_json["regionName"],
                    "is_proxy": response_json["proxy"],
                    "is_hosting": response_json["hosting"],
                    "is_mobile": response_json["mobile"],
                    "reverseDNS": response_json["reverse"] if response_json["reverse"] else "N/A",
                    "last_seen": str(datetime.now(UTC))
                }

            with open(self.log_path, "w") as f:
                f.write(json.dumps(data, indent=4))

            await self.app(scope, receive, send)
            return

        # TOML FORMAT HANDLING
        elif self.file_format == "TOML":
            # Check if the TOML log file already exists and already stores the data for the IP, if so, only update the time
            if Path(self.log_path).exists() and Path(self.log_path).is_file():
                with open(self.log_path, "r") as f:
                    try:
                        data = tomllib.loads(f.read())
                    except Exception:
                        if f.read():
                            raise Exception(f"The given log file {self.log_path} does not contain valid TOML")

                # Status code errors (!= 200) need to be retried since they're caused by stuff like rate limits (429),
                # but errors caused by 'status' key not being 'success' don't need to be tried because
                # they're caused by things like private, reserved IP range and invalid query, so we are verifying
                # either the message key is absent (all necessary data gathered) or exists but doesn't start with
                # "Status code: " meaning not a status code error so it doesn't need to be retried hence we can safely
                # retain the already present data and only update the last_seen key

                if (data.get(ip) and not data.get(ip).get("detail")) or (data.get(ip) and data.get(ip).get("detail") and not data.get(ip).get("detail").startswith("Status code: ")):
                    # Update the last seen only, use ISO 8601 time format
                    data[ip]["last_seen"] = str(datetime.now(UTC))

                    with open(self.log_path, "w") as g:
                        g.write(tomli_w.dumps(data, indent=4) + "\n")

                    # Also log even when data is already stored if logging enabled
                    # Check if message key is absent which implies the request stored in logs has all necessary
                    # data, so well use that for logging
                    if self.log_to_console and not data.get(ip).get("detail"):
                        stored_data = data[ip]
                        logging.info(f"""
                            IP: {ip}
                            Country: {stored_data["country"]}
                            Continent: {stored_data["continent"]}
                            Proxy: {stored_data["is_proxy"]}
                            """)

                    await self.app(scope, receive, send)
                    return

            # If not, send request
            async with httpx.AsyncClient() as client:
                ip = scope["client"][0]
                response = await client.get(
                    f"http://ip-api.com/json/{ip}?fields=status,country,continent,city,regionName,proxy,hosting,mobile,reverse")
                response_json = response.json()

            # Immediately log to console if console logging is enabled
            if self.log_to_console:
                if response_json["status"] != "success" or response.status_code != 200:
                    logging.warning(
                        f"IP lookup for \'{ip}\' failed, status code: {response.status_code}" if response.status_code != 200 else f"IP lookup for \'{ip}\' failed, \'status\' key wasn't \'success\'")
                else:
                    logging.info(f"""
                    IP: {ip}
                    Country: {response_json["country"]}
                    Continent: {response_json["continent"]}
                    Proxy: {response_json["proxy"]}
                    """)


            # Log to file and stuff
            if response_json["status"] != "success" or response.status_code != 200:
                data[ip]  = {
                      "detail": "IP lookup failed",
                      "reason":  "\'status\' key wasn't \'success\'" if response_json["status"] != "success" else f"Status code: {response.status_code}",
                      "last_seen": str(datetime.now(UTC))
                  }
            else:
                data[ip] = {
                        "country": response_json["country"],
                        "continent": response_json["continent"],
                        "city": response_json["city"],
                        "region": response_json["regionName"],
                        "is_proxy": response_json["proxy"],
                        "is_hosting": response_json["hosting"],
                        "is_mobile": response_json["mobile"],
                        "reverseDNS": response_json["reverse"] if response_json["reverse"] else "N/A",
                        "last_seen": str(datetime.now(UTC))
                    }


            with open(self.log_path, "w") as f:
                f.write(tomli_w.dumps(data) + "\n")

            await self.app(scope, receive, send)
            return
