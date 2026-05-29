from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import google.generativeai as genai
import os
import base64

class Command(BaseCommand):
    help = 'Process menu images using AI APIs'

    def handle(self, *args, **options):
        load_dotenv()
        
        img_path = os.path.join(os.path.dirname(__file__), 'downloads', 'c.png')
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-3.5-flash')
        
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
                {"text": "{'main': '만두라면, 치즈라면', 'side': None, 'price': 3000, 'calendar': None, 'time_category': ['아침', '저녁'], 'time_detail': {'아침': ['09:00', '10:00'], '저녁': ['17:30', '18:30']}, 'place': '청운관 학생식당', 'extra': None, 'non_pork': False}처럼 메뉴를 정리해주세요"}
            ]
            
            response = model.generate_content(contents)
            self.stdout.write(f'Gemini response: {response.text}')
                            
        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Error: {err}'))