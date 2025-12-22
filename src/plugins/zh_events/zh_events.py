from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
# REMOVED: from playwright.sync_api import sync_playwright
import json
from PIL import Image, ImageDraw, ImageFont
from utils.image_utils import resize_image
from datetime import datetime, timedelta
from pathlib import Path
import time
import logging
import random
import subprocess
import shutil
from bs4 import BeautifulSoup

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
        logger.info(f"Scraping {url} using Chromium dump-dom...")
        
        # 1. Detect the binary robustly
        chromium_bin = "chromium-headless-shell"
        
        # Check standard paths (Pi)
        if not shutil.which(chromium_bin):
            chromium_bin = "chromium-browser"
        
        # Optional: Check for local Mac binary if running in dev environment
        # This keeps it working on your Mac without breaking the Pi logic
        current_dir = Path(__file__).parent.resolve()
        mac_binary_path = current_dir / "../chrome-headless-shell-mac-arm64/chrome-headless-shell"
        if mac_binary_path.exists():
            chromium_bin = str(mac_binary_path.resolve())

        # 2. Prepare the command
        command = [
            chromium_bin,
            "--headless",
            "--dump-dom",
            "--disable-gpu",
            "--no-sandbox", # Essential for running as root/docker
            "--disable-dev-shm-usage", # Essential for Pi low memory
            "--virtual-time-budget=15000", # Allow 15s for JS to execute
            url
        ]

        try:
            # 3. Execute Chromium
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True
            )
            html_content = result.stdout

        except subprocess.CalledProcessError as e:
            logger.error(f"Chromium scraping failed: {e}")
            logger.error(e.stderr)
            return []
        except FileNotFoundError:
            logger.error(f"Chromium binary '{chromium_bin}' not found. Please install chromium-browser.")
            return []

        # 4. Parse output with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        items = soup.select('.cp-teaser-box-item-kz')

        for item in items:
            try:
                # -- Image --
                image_el = item.select_one('.image-container img')
                image_src = None
                if image_el and image_el.has_attr('src'):
                    src = image_el['src']
                    if src.startswith('/'):
                        image_src = f"https://kulturzueri.ch{src}"
                    else:
                        image_src = src

                # -- Title & URL --
                title_el = item.select_one('.title')
                title_text = title_el.get_text(strip=True) if title_el else None
                title_url = title_el['href'] if title_el and title_el.has_attr('href') else None

                # -- Location --
                location_el = item.select_one('.el-location')
                location_text = location_el.get_text(strip=True) if location_el else None

                # -- Details (Description, Date, Time) --
                teaser_container = item.select_one('.teaser-text-container')
                desc_text = None
                date_text = None
                time_text = None

                if teaser_container:
                    # Description is usually the first paragraph inside teaser
                    desc_el = teaser_container.find('p')
                    desc_text = desc_el.get_text(strip=True) if desc_el else None
                    
                    date_el = teaser_container.select_one('.date')
                    date_text = date_el.get_text(strip=True) if date_el else None
                    
                    time_el = teaser_container.select_one('.time')
                    time_text = time_el.get_text(strip=True) if time_el else None

                # Only add if we have a title
                if title_text:
                    events.append({
                        "title": title_text,
                        "url": title_url,
                        "image": image_src,
                        "location": location_text,
                        "description": desc_text,
                        "date": date_text,
                        "time": time_text
                    })

            except Exception as e:
                logger.warning(f"Error parsing a single event item: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(events)} events.")
        return events
        
    @classmethod
    def load_cache(cls):
        if cls.CACHE_FILE.exists():
            try:
                with open(cls.CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data['last_scraped'] = datetime.fromisoformat(data['last_scraped'])
                    return data
            except (json.JSONDecodeError, ValueError):
                logger.warning("Cache file corrupted, resetting cache.")
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
            if exhibits:
                cls.save_cache(exhibits)
            else:
                logger.warning("Scrape returned no results, using empty cache or old data if available.")
        else:
            logger.info("Using cached exhibits...")
            exhibits = cache["exhibits"]

        return exhibits
        
    @staticmethod
    def select_random_exhibit(exhibits):
        if not exhibits:
            return None
        return random.choice(exhibits)