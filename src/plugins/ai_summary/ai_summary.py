from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
from google import genai
import feedparser
from PIL import Image, ImageDraw, ImageFont
from utils.image_utils import resize_image
from io import BytesIO
from datetime import datetime, timedelta
import time
import requests
import logging
import textwrap
import os

logger = logging.getLogger(__name__)

class AISummary(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['api_key'] = {
            "required": True,
            "service": "Gemini",
            "expected_key": "GEMINI_SECRET"
        }
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):
        api_key = device_config.load_env_key("GEMINI_SECRET")
        if not api_key:
            raise RuntimeError("Gemini API Key not configured.")

        title = settings.get("title")

        text_model = settings.get('textModel') # need to add the correct models in the HTML I think !!!
        if not text_model:
            raise RuntimeError("Text Model is required.")
        
        rss_feeds = settings.get('rssFeeds[]')
        if not rss_feeds:
            raise RuntimeError("At least one RSS feed is required")
        for rss_feed in rss_feeds:
            if not rss_feed.strip():
                raise RuntimeError("Invalid RSS link")
            
        base_prompt = settings.get('basePrompt')
        if not base_prompt:
            raise RuntimeError("A base prompt is required to generate the rss feed summary.")

        try:
            ai_client = genai.Client(api_key = api_key)
            prompt_response = AISummary.fetch_text_prompt(ai_client, text_model, rss_feeds, base_prompt)
        except Exception as e:
            logger.error(f"Failed to make Gemini request: {str(e)}")
            raise RuntimeError("Gemini request failure, please check logs.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": title,
            "content": prompt_response,
            "plugin_settings": settings
        }
        
        image = self.render_image(dimensions, "ai_summary.html", "ai_summary.css", image_template_params)

        return image
    
    @staticmethod
    def fetch_rss_last_2_days(url):
        feed = feedparser.parse(url)

        # get channel metadata 
        channel_title = feed.feed.get("title", "")
        channel_desc = feed.feed.get("description", "")

        # Filter items from last 2 days
        items = []
        two_days_ago = datetime.now() - timedelta(days=2)

        for entry in feed.entries:
            if "published_parsed" not in entry:
                continue # skip old articles

            published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if published_dt < two_days_ago:
                continue

            items.append({
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "published": entry.get("published", "")
            })

        return {
            "channel_title": channel_title,
            "channel_description": channel_desc,
            "items": items
        }
    
    @staticmethod
    def fetch_text_prompt(ai_client, model, rss_feeds, base_prompt):
        logger.info(f"Getting rss feeds and parsing them to AI model: {model}")

        full_base_prompt = (
            base_prompt + 
            f"For context, today is {datetime.today().strftime('%Y-%m-%d')}"
        )

        rss_prompt = ""
        for rss_feed in rss_feeds:
            rss_dict = AISummary.fetch_rss_last_2_days(rss_feed)
            rss_prompt += " | " + str(rss_dict)

        full_prompt = full_base_prompt + rss_prompt

        # Make the API call
        response = ai_client.models.generate_content(model=model, contents=full_prompt)

        response_text = response.candidates[0].content.parts[0].text

        logger.info(f"Generated the news summary: {response_text}")
        return response_text