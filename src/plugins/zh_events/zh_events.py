from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
from playwright.sync_api import sync_playwright
import json
from PIL import Image, ImageDraw, ImageFont
from utils.image_utils import resize_image
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging
import random

logger = logging.getLogger(__name__)

class ZHEvents(BasePlugin):

    CACHE_FILE = Path(__file__).parent / "kulturzueri_cache.json"
    SCRAPE_INTERVAL = timedelta(days=7)
    
    def generate_image(self, settings, device_config):
        try:
            exhibits = ZHEvents.get_exhibits()
            random_exhibit = ZHEvents.select_random_exhibit(exhibits)

            if random_exhibit:
                exhibit_data = {
                    "title": random_exhibit.get("title") or "No title",
                    "image": random_exhibit.get("image"),
                    "description": random_exhibit.get("description") or "",
                    "location": random_exhibit.get("location") or "Unknown",
                    "date": random_exhibit.get("date") or "",
                    "time": random_exhibit.get("time") or ""
                }
            else:
                raise RuntimeError("No exhibits available")
        except Exception as e:
            logger.error(f"Failed to load exhibits: {str(e)}")
            raise RuntimeError("Failed to load exhibits. Check logs.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": exhibit_data["title"],
            "image": exhibit_data["image"],
            "description": exhibit_data["description"],
            "location": exhibit_data["location"],
            "date": exhibit_data["date"],
            "time": exhibit_data["time"],
            "plugin_settings": settings
        }
        
        image = self.render_image(dimensions, "zh_events.html", "zh_events.css", image_template_params)

        return image
    
    @staticmethod
    def scrape_kulturzueri(url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)
            page.wait_for_selector(".cp-teaser-box-item-kz", timeout=30000)

            events = page.evaluate("""
                () => Array.from(document.querySelectorAll('.cp-teaser-box-item-kz')).map(item => {
                    const imageEl = item.querySelector('.image-container img');
                    const titleEl = item.querySelector('.title');
                    const locationEl = item.querySelector('.el-location');

                    const teaserContainer = item.querySelector('.teaser-text-container');
                    const descEl = teaserContainer ? teaserContainer.querySelector('p') : null;
                    const dateEl = teaserContainer ? teaserContainer.querySelector('.date') : null;
                    const timeEl = teaserContainer ? teaserContainer.querySelector('.time') : null;

                    return {
                        title: titleEl ? titleEl.innerText.trim() : null,
                        url: titleEl ? titleEl.href : null,
                        image: imageEl ? imageEl.src : null,
                        location: locationEl ? locationEl.innerText.trim() : null,
                        description: descEl ? descEl.innerText.trim() : null,
                        date: dateEl ? dateEl.innerText.trim() : null,
                        time: timeEl ? timeEl.innerText.trim() : null
                    };
                })
            """)

            browser.close()
            return events
        
    @classmethod
    def load_cache(cls):
        if cls.CACHE_FILE.exists():
            with open(cls.CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data['last_scraped'] = datetime.fromisoformat(data['last_scraped'])
                return data
        return {"last_scraped": datetime.min, "exhibits": []}
    
    @classmethod
    def save_cache(cls, exhibits):
        data = {
            "last_scraped": datetime.now().isoformat(),
            "exhibits": exhibits
        }
        with open(cls.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_exhibits(cls):
        cache = cls.load_cache()

        if datetime.now() - cache["last_scraped"] > cls.SCRAPE_INTERVAL or not cache["exhibits"]:
            logger.info("Scraping kulturzueri website for exhibits...")
            exhibits = cls.scrape_kulturzueri("https://kulturzueri.ch/ausstellungen/")
            cls.save_cache(exhibits)
        else:
            logger.info("Using cached exhibits...")
            exhibits = cache["exhibits"]

        return exhibits
        
    @staticmethod
    def select_random_exhibit(exhibits):
        if not exhibits:
            return None
        return random.choice(exhibits)

        
    
            
        