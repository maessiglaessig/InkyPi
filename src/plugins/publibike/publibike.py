from plugins.base_plugin.base_plugin import BasePlugin
from datetime import datetime
import requests
import logging
import pytz

logger = logging.getLogger(__name__)

class Publibike(BasePlugin):
    STATIONS_URL = "https://rest.publibike.ch/v1/public/all/stations"

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['style_settings'] = True

        try:
            stations = Publibike.fetch_stations().values()
            template_params['stations'] = sorted(
                ({"number": s.get("stationNumber"), "name": s.get("station_name", ""), "address": s.get("station_address", "")}
                 for s in stations),
                key=lambda s: s["name"].lower()
            )
        except Exception as e:
            logger.error(f"Failed to load Publibike stations for settings: {str(e)}")
            template_params['stations'] = []
        return template_params

    def generate_image(self, settings, device_config):
        station_numbers = [settings.get("station1"), settings.get("station2")]
        station_numbers = [n.strip() for n in station_numbers if n and n.strip()]
        if not station_numbers:
            raise RuntimeError("At least one station is required.")

        try:
            stations = Publibike.fetch_stations()
        except Exception as e:
            logger.error(f"Failed to fetch Publibike stations: {str(e)}")
            raise RuntimeError("Publibike request failure, please check logs.")

        panes = []
        for i, number in enumerate(station_numbers, start=1):
            station = stations.get(number)
            if not station:
                name = settings.get(f"station{i}Name") or "unknown"
                raise RuntimeError(f"Station {name} ({number}) not found.")
            panes.append({
                "name": station.get("station_name", ""),
                "address": station.get("station_address", ""),
                "total": Publibike.to_int(station.get("totalBike")),
                "normal": Publibike.to_int(station.get("totalNonElectricalBike")),
                "electric": Publibike.to_int(station.get("totalElectricalBike"))
            })

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        timezone = device_config.get_config("timezone", default="America/New_York")
        updated = datetime.now(pytz.timezone(timezone)).strftime("%H:%M")

        image_template_params = {
            "title": settings.get("title", "").strip() if settings.get("showTitle", "true") == "true" else "",
            "panes": panes,
            "layout": "row" if dimensions[0] >= dimensions[1] else "column",
            "updated": updated,
            "plugin_settings": settings
        }

        image = self.render_image(dimensions, "publibike.html", "publibike.css", image_template_params)

        return image

    @classmethod
    def fetch_stations(cls):
        """Returns all Velospot stations keyed by stationNumber."""
        response = requests.get(cls.STATIONS_URL, timeout=20)
        response.raise_for_status()

        stations = (response.json().get("velospot") or {}).get("responseData")
        if not isinstance(stations, list):
            raise RuntimeError("Unexpected response format from Publibike API.")
        return {str(s.get("stationNumber")): s for s in stations}

    @staticmethod
    def to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
