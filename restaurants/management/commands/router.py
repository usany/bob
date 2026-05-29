from django.core.management.base import BaseCommand
from google import genai
import os
import base64
import ast
import re
import json
from restaurants.models import MenuItem

class Command(BaseCommand):
    help = 'Process menu images using AI APIs'

    def handle(self, *args, **options):
        
        img_path = os.path.join(os.path.dirname(__file__), 'downloads', 'c.png')
        client = genai.Client(api_key='AIzaSyAjdTDl2FpSyJN0HNrOgxUzCk4DhgHJz6I')

        
        try:
            # Read image and convert to base64
            with open(img_path, 'rb') as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            # Gemini API call
            contents = [
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64_image,
                    },
                },
                {"text": "{'main': '낙지콩나물덮밥', 'side': '유부장국, 유린기 닭:브라질산, 중화품배추찜, 마카로니크래미샐러드, 고들빼기무침, 마시는 요구르트', 'price': 8000, 'time': 'lunch', 'day': 'tue', 'place': 'cg', 'extra_menu': '', 'extra_price': 0, 'non_pork': False, 'storage_url': '/낙지콩나물덮밥.png'}처럼 각 메뉴를 정리해주세요. place는 청운관 학생식당: ch, 청운관 교직원식당: cg, 푸른솔 학생식당: ph, 푸른솔 교직원식당: pg, 학생회관 학생식당: hh, 학생회관 교직원식당: hg입니다. py list로 만들고 # 메모 없이 작성해주세요."},
            ]
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=contents)
            self.stdout.write(f'Gemini response: {response.text}')
            
            # Strip markdown code fences if present, then parse into a list
            raw = response.text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[-1]          # drop opening fence line
                raw = raw.rsplit('```', 1)[0].strip()  # drop closing fence

            # Convert Python literals to JSON-compatible format
            raw = raw.replace("True", "true").replace("False", "false").replace("None", "null")
            # Replace single quotes with double quotes (handle escaped single quotes first)
            raw = re.sub(r"(?<!\\)'", '"', raw)

            parsed = json.loads(raw)
            # Normalise to list whether Gemini returns a single dict or a list
            collection = parsed if isinstance(parsed, list) else [parsed]
            
            for index, menu in enumerate(collection):
                MenuItem.objects.create(
                    main=menu.get('main', ''),
                    side=menu.get('side', ''),
                    price=menu.get('price', 0),
                    time=menu.get('time', ''),
                    day=menu.get('day', ''),
                    place=menu.get('place', ''),
                    extra_menu=menu.get('extra_menu', ''),
                    extra_price=menu.get('extra_price', 0),
                    non_pork=menu.get('non_pork', False),
                    storage_url=menu.get('storage_url', ''),
                )
                self.stdout.write(self.style.SUCCESS(f"Successfully posted item: {menu.get('main', 'Unknown Menu Item')}"))
        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Error: {err}'))