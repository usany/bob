from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
import os
import base64


class Command(BaseCommand):
    help = 'Process menu images using AI APIs'

    def handle(self, *args, **options):
        load_dotenv()
        
        img_path = os.path.join(os.path.dirname(__file__), 'downloads', 'c.png')
        
        openai_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv('NVIDIA_NIM_API_KEY'),
        )
        
        selection = "nvidia/nemotron-nano-12b-v2-vl"
        
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
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
            
            # OpenAI API call
            try:
                response = openai_client.chat.completions.create(
                    model=selection,
                    messages=[
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': "파일 이미지에 쓰여 있는 대로만 음식 메뉴를 정확히 추출해 ## 푸른솔 교직원식당 * 푸른솔 소담(교직원식당) 11:00~14:00 * 푸른솔 교직원식당 11:00~14:00 * 푸른솔 비빔코너(교직원식당) 11:00~14:00 ## 푸른솔 학생식당 * 푸른솔 조식(학생식당) 08:00~09:30 * 푸른솔 중식 One Dish(학생식당) 11:00~14:30 세트/셀프바 * 푸른솔 중식 한소반(학생식당) 11:00~14:30 세트/셀프 * 푸른솔 TO-GO(One Dish) 08:30~16:00 * 푸른솔 셀프조리(One Dish) 08:30~16:00 토핑 * 푸른솔 TO-GO(무인판매) 월~목 14:30~16:00 로 메뉴를 정리해주세요"
                                },
                                {
                                    'type': 'image_url',
                                    'image_url': {'url': f'data:image/jpeg;base64,{base64_image}'},
                                },
                            ],
                        },
                    ],
                )
                self.stdout.write(f'OpenAI response: {response.choices[0].message.content}')
            except Exception as err:
                self.stderr.write(self.style.ERROR(f'OpenAI error: {err}'))
                
        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Error: {err}'))