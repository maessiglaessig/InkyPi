from plugins.base_plugin.base_plugin import BasePlugin
from datetime import datetime
from pathlib import Path
import logging
import random
import json
import pytz

logger = logging.getLogger(__name__)

class DailyText(BasePlugin):
    TEXT_FILE = Path(__file__).parent / "daily_text.json"
    DEFAULT_COLLECTION = "affirmations"

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):
        collection = settings.get("collection") or DailyText.DEFAULT_COLLECTION
        pool = DailyText.build_pool(collection, settings)
        if not pool:
            raise RuntimeError(f"No entries found for collection '{collection}'.")

        timezone = device_config.get_config("timezone", default="America/New_York")
        today = datetime.now(pytz.timezone(timezone)).date()
        entry = DailyText.select_daily_entry(pool, collection, today)

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": settings.get("title", "").strip(),
            "text": entry["text"],
            "author": entry.get("author"),
            "plugin_settings": settings
        }

        image = self.render_image(dimensions, "daily_text.html", "daily_text.css", image_template_params)

        return image

    @classmethod
    def load_collections(cls):
        if not cls.TEXT_FILE.exists():
            raise RuntimeError(f"Text file not found: {cls.TEXT_FILE}")
        with open(cls.TEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("collections", {})

    @staticmethod
    def build_pool(collection, settings):
        """Returns a list of {"text", "author"} dicts from the chosen collection plus custom entries."""
        custom_entries = [
            {"text": line.strip()}
            for line in settings.get("customEntries", "").splitlines()
            if line.strip()
        ]
        if settings.get("onlyCustom") == "true":
            return custom_entries

        collections = DailyText.load_collections()
        if collection == "mixed":
            entries = [e for c in collections.values() for e in c]
        else:
            entries = collections.get(collection, [])

        pool = [e if isinstance(e, dict) else {"text": e} for e in entries]
        return pool + custom_entries

    @staticmethod
    def select_daily_entry(pool, seed, date):
        """Picks one entry per day. Shuffle order is fixed per seed, so entries
        don't repeat until the whole pool has been shown."""
        shuffled = sorted(pool, key=lambda e: e["text"])
        random.Random(seed).shuffle(shuffled)
        return shuffled[date.toordinal() % len(shuffled)]
