from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
from PIL import Image
from utils.image_utils import resize_image
from datetime import datetime
import requests
import logging
import random

logger = logging.getLogger(__name__)

class Movierecs(BasePlugin):
    # Class variable to track the current index across multiple executions/refreshes
    _current_index = 0

    def generate_settings_template(self):
        template_params = super().generate_settings_template()

        template_params['api_key'] = {
            "required": True,
            "service": "OMDB",
            "expected_key": "OMDB_SECRET"
        }

        template_params['movie_titles[]'] = {
            "required": True,
            "placeholder": "e.g. Fallen Angels",
            "label": "Movie Titles (one per field)"
        }

        template_params['style_settings'] = True

        return template_params


    def generate_image(self, settings, device_config):
        """Display ONE random movie from list using OMDB."""
        api_key = device_config.load_env_key("OMDB_SECRET")
        if not api_key:
            raise RuntimeError("OMDB API Key not configured in .env")
        
        title = settings.get("title")

        # Load settings array as list of strings
        titles = settings.get("movie_titles[]")
        if not titles:
            raise RuntimeError("At least one movie title is required")

        titles = [t.strip() for t in titles if t.strip()]
        if not titles:
            raise RuntimeError("Movie title fields are empty")

        # Fetch data for each movie and store only valid ones
        movie_data = []
        for title in titles:
            data = Movierecs.fetch_movie_data(title, api_key)
            if data:
                movie_data.append(data)

        if not movie_data:
            raise RuntimeError("No valid movies found, check titles!")

        # choose movie based on the current cycle indexx
        # use module to loop back to the start if the index esceeds the list length
        current_selection_index = Movierecs._current_index % len(movie_data)
        selected_movie = movie_data[current_selection_index]

        # increment the index for the next refresh
        Movierecs._current_index += 1

        # Orientation correction
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": selected_movie["title"],
            "plot": selected_movie["plot"],
            "released": selected_movie["released"],
            "rating": selected_movie["rating"],
            "poster": selected_movie["poster_url"],
            "box_office": selected_movie["box_office"],
            "plugin_settings": settings
        }

        # Render a SINGLE-movie template
        image = self.render_image(dimensions, "movie_recs.html", "movie_recs.css", image_template_params)

        return image


    @staticmethod
    def fetch_movie_data(title, api_key):
        url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}&plot=full"
        resp = requests.get(url)

        if resp.status_code != 200:
            logger.error(f"OMDB error for: {title}")
            return None

        data = resp.json()
        if data.get("Response") == "False":
            logger.warning(f"Movie not found: {title}")
            return None

        return {
            "title": data.get("Title", "Unknown"),
            "plot": data.get("Plot", "").strip(),
            "released": data.get("Released", ""),
            "rating": data.get("imdbRating", "N/A"),
            "poster_url": data.get("Poster", None),
            "box_office": data.get("BoxOffice", "N/A")
        }
