from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path
from PIL import Image
from utils.image_utils import resize_image
from datetime import datetime
from pathlib import Path
import requests
import logging
import random
import json

logger = logging.getLogger(__name__)

class ReflectionPrompts(BasePlugin):
    # class variable to track the current prompt category
    _current_category_index = 0
    # class variable to get prompts
    PROMPT_FILE = Path(__file__).parent / "reflection_prompts.json"

    def generate_settings_template(self):
        return super().generate_settings_template()
    
    def generate_image(self, settings, device_config):
        try:
            # 1. Load the data using your class method
            data = ReflectionPrompts.get_reflection_prompt()
            # Get the actual 'prompts' dictionary from the JSON
            prompts_dict = data.get("prompts", {})
            # Create a list of the keys (the categories)
            categories = list(prompts_dict.keys())

            if not categories:
                raise RuntimeError("No categories found in JSON")

            # 2. Get the current category using the index
            category = categories[ReflectionPrompts._current_category_index]
            
            # 3. Get a random prompt from that specific category
            prompt = ReflectionPrompts.select_random_prompt(prompts_dict[category])

            # 4. Correct way to increment and reset the index
            # This replaces the line that caused the error
            ReflectionPrompts._current_category_index += 1
            if ReflectionPrompts._current_category_index >= len(categories):
                ReflectionPrompts._current_category_index = 0
        except Exception as e:
            logger.error(f"Failed to load prompt: {str(e)}")
            raise RuntimeError("Failed to load prompt. Check logs.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        image_template_params = {
            "title": "Prompt of the Day",
            "content": prompt,
            "plugin_settings": settings
        }
        
        image = self.render_image(dimensions, "reflection_prompts.html", "reflection_prompts.css", image_template_params)

        return image
    
    
    @classmethod
    def get_reflection_prompt(cls):
        if cls.PROMPT_FILE.exists():
            with open(cls.PROMPT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
            
    @staticmethod
    def select_random_prompt(prompts):
        if not prompts:
            return None
        return random.choice(prompts)
        
    