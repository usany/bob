from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
import os
import pathlib
from restaurants.models import MenuItem
import random
from concurrent.futures import ThreadPoolExecutor 
import requests
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Generate an image using Cloudflare AI'

    def handle(self, *args, **options):
        load_dotenv()
        account_id = os.getenv('CFACCOUNTID')
        api_token = os.getenv('CFAPITOKEN')

        if not account_id or not api_token:
            self.stderr.write(self.style.ERROR('Cloudflare credentials not found in environment variables.'))
            return

        prompt = "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
        # url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "seed": random.randint(0, 1000000),
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                with open("output.png", "wb") as f:
                    f.write(response.content)
                self.stdout.write(self.style.SUCCESS("Image saved as output.png"))
            else:
                self.stderr.write(self.style.ERROR(f"Cloudflare API error: {response.status_code} {response.text}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating image: {str(e)}"))
