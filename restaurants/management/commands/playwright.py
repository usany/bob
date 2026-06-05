from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
import os
import pathlib
from restaurants.models import MenuItem
import random
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from google import genai as google_genai
import mimetypes
import base64
import re
import json
import uuid

class Command(BaseCommand):
    help = 'Scrape menu data from university websites using Playwright'
    storage_url = os.getenv('STORAGE_URL', 'https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['khu', 'hufs', 'dorm'],
            help='Source to scrape: khu, hufs, or dorm'
        )
        parser.add_argument(
            '--campus',
            type=str,
            choices=['seoul', 'global'],
            help='Campus for KHU: seoul or global'
        )
        parser.add_argument(
            '--student',
            action='store_true',
            help='Use student menu for HUFS'
        )

    def handle(self, *args, **options):
        source = options.get('source')
        campus = options.get('campus')
        is_student = options.get('student')

        if not source:
            self.stdout.write(self.style.ERROR('Please specify --source (khu, hufs, or dorm)'))
            return

        with sync_playwright() as p:
            if source == 'dorm':
                self.scrap_dorm(p)
            elif source == 'hufs':
                self.scrap_hufs(p, is_student)
            elif source == 'khu':
                if not campus:
                    self.stdout.write(self.style.ERROR('Please specify --campus (seoul or global) for KHU'))
                    return
                is_seoul = campus == 'seoul'
                self.scrap(p, is_seoul)

    def scrap_dorm(self, playwright):
        """Scrape dorm menu"""
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        self.stdout.write('Navigating to the list page...')
        link = 'https://dorm2.khu.ac.kr/50/5030.do#'
        page.goto(link)
        
        page.locator('a').filter(has_text='전체보기').first.click()
        page.wait_for_selector('td.te_left')
        
        menu_texts = page.locator('td.te_left').all_inner_texts()
        self.stdout.write(str(menu_texts))
        self.stdout.write(f'Found {len(menu_texts)} items')
        
        browser.close()
        
        # Create MenuItem objects outside of Playwright context
        def create_menu_items():
            place = 'jg'
            for index, menu in enumerate(menu_texts):
                if (menu == '미운영'):
                    continue
                if (menu.startswith('A코너 : ')):
                    first_part = menu.split(' : ', 1)[1]
                    first_menu = first_part.split(',', 1)
                    main = first_menu[0].strip() if first_menu else ''
                    side = first_menu[1].split('B코너 : ', 1)[0].strip() if len(first_menu) > 1 else ''
                    MenuItem.objects.create(
                        id=str(uuid.uuid4()),
                        main=main,
                        side=side,
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        meal='lunch',
                        place=place,
                        price=6500,
                        extra='',
                        date=None,
                        stamp=False,
                    )
                    
                    self.generate_image(main)

                    second_part = first_menu[1].split('B코너 : ', 1)[1].strip() if len(first_menu) > 1 else ''
                    second_menu = second_part.split(',', 1)
                    main = second_menu[0].strip() if second_menu else ''
                    side = second_menu[1].strip() if len(second_menu) > 1 else ''
                    MenuItem.objects.create(
                        id=str(uuid.uuid4()),
                        main=main,
                        side=side,
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        meal='lunch',
                        place=place,
                        price=5500,
                        extra='',
                        date=None,
                        stamp=False,
                    )
                    self.generate_image(main)

                else:
                    menu_parts = menu.split(',', 1)
                    main = menu_parts[0].strip() if menu_parts else ''
                    side = menu_parts[1].strip() if len(menu_parts) > 1 else ''
                    meal = 'breakfast' if index % 3 == 0 else 'dinner'
                    MenuItem.objects.create(
                        id=str(uuid.uuid4()),
                        main=main,
                        side=side,
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        meal=meal,
                        place=place,
                        price=5500,
                        extra='',
                        date=None,
                        stamp=False,
                    )
                    self.generate_image(main)

        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(create_menu_items).result()

    def scrap_hufs(self, playwright, is_student):
        """Scrape HUFS menu"""
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        self.stdout.write('Navigating to the list page...')
        link = 'https://www.hufs.ac.kr/hufs/11318/subview.do#click'
        # if is_student:
        #     link = 'https://www.hufs.ac.kr/hufs/11318/subview.do#click'
        # else:
        #     link = 'https://www.hufs.ac.kr/hufs/11318/subview.do?enc=Zm5jdDF8QEB8JTJGY2FmZXRlcmlhJTJGaHVmcyUyRjElMkZ2aWV3LmRvJTNGeWVhciUzRDIwMjYlMjZtb250aCUzRDA1JTI2c2VsRGF0ZSUzRDIwMjYwNTIxJTI2c2VsQ2FmSWQlM0RoMTAyJTI2'
        page.goto(link)
        if not is_student:
            page.locator('a').filter(has_text='교수회관식당').click()
            # page.wait_for_selector('td.no-menu, td.menu')
        page.wait_for_selector('td.no-menu, td.menu')
                    
        menu_texts = page.locator('td.no-menu, td.menu').all_inner_texts()
        self.stdout.write(str(menu_texts))
        self.stdout.write(f'Found {len(menu_texts)} items')

        browser.close()

        # Create MenuItem objects outside of Playwright context
        def create_menu_items():
            for index, menu in enumerate(menu_texts):
                if menu.startswith('등록된') or index % 7 < 1 or index % 7 > 5:
                    continue
                menu_parts = menu.split('\n')
                main = menu_parts[0].strip() if menu_parts else ''
                side = menu_parts[1].strip() if len(menu_parts) > 1 else ''
                if not main or not side:
                    continue
                place = 'hi' if is_student else 'hg'
                meal = 'lunch' if not is_student else 'breakfast' if index < 7 else 'lunch' if index < 28 else 'dinner'
                day = 'mon' if index % 7 == 1 else 'tue' if index % 7 == 2 else 'wed' if index % 7 == 3 else 'thu' if index % 7 == 4 else 'fri'
                existing = MenuItem.objects.filter(
                    main=main,
                    side=side,
                    day=day,
                    meal=meal,
                    place=place,
                ).first()
                if existing:
                    existing.price = int(menu_parts[-1].split('(')[0].replace(',', '').replace('원', ''))
                    existing.save()
                else:
                    MenuItem.objects.create(
                        id=str(uuid.uuid4()),
                        main=main,
                        side=side,
                        day=day,
                        meal=meal,
                        place=place,
                        price=int(menu_parts[-1].split('(')[0].replace(',', '').replace('원', '')),
                        extra='',
                        date=None,
                        stamp=False,
                    )
                self.generate_image(main)

        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(create_menu_items).result()
        

    def scrap(self, playwright, is_seoul=True):
        """Scrape KHU menu and download images"""
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        self.stdout.write('Navigating to the list page...')
        if is_seoul:
            link = 'https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283&catId=136'
        else:
            link = 'https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283&catId=137'
        
        page.goto(link)
        page.wait_for_selector('tbody')
        
        # Find links in tbody - map over locations to find matching elements
        locations = ['푸른솔', '청운관'] if is_seoul else ['학생회관', '기숙사']
        raw_links = []
        
        for loc in locations:
            element = page.locator('tbody a').filter(has_text=loc).first
            if element.count() > 0:
                raw_links.append({
                    'href': element.get_attribute('href'),
                    'text': element.inner_text().strip(),
                    'onclick': element.get_attribute('onclick')
                })
        
        self.stdout.write(f'Found {len(raw_links)} links in tbody.')
        
        # Create download directory
        download_dir = pathlib.Path(__file__).parent / 'downloads'
        download_dir.mkdir(exist_ok=True)
        
        for link_data in raw_links:
            if not link_data['href'] or link_data['href'].startswith('javascript:'):
                self.stdout.write(f'Handling link: {link_data["text"]}')
                
                if page.url != link:
                    page.goto(link)
                    page.wait_for_selector('tbody')
                
                try:
                    with page.expect_navigation(wait_until='domcontentloaded'):
                        page.locator('tbody a').filter(has_text=link_data['text']).first.click()
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f'Failed to navigate to {link_data["text"]}: {str(err)}'))
                    continue
            else:
                self.stdout.write(f'Visiting URL: {link_data["href"]}')
                try:
                    page.goto(link_data['href'], wait_until='domcontentloaded')
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f'Failed to visit {link_data["href"]}: {str(err)}'))
                    continue
            
            title = page.locator('p.txt06').first.inner_text().strip()
            
            # Find PNG images
            images = page.locator('img').all()
            image_urls = []
            for img in images:
                src = img.get_attribute('src')
                if src and src.endswith('.png') and 'decoGnb' not in src and 'footLogo' not in src and 'ico' not in src:
                    image_urls.append(src)
            
            self.stdout.write(f'Found {len(image_urls)} PNG images on this page.')
            
            for img_url in image_urls:
                try:
                    absolute_img_url = page.url + img_url if not img_url.startswith('http') else img_url
                    
                    if '청운관' in title:
                        image_name = 'c.png'
                    elif '푸른솔' in title:
                        image_name = 'p.png'
                    elif '학생회관' in title:
                        image_name = 'h.png'
                    else:
                        image_name = 'j.png'
                    
                    local_path = download_dir / image_name
                    
                    response = page.request.get(absolute_img_url)
                    if response.status == 200:
                        local_path.write_bytes(response.body())
                        self.stdout.write(self.style.SUCCESS(f'Downloaded: {image_name}'))
                        self.get_menu(str(local_path))
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f'Failed to download image {img_url}: {str(err)}'))
            
            # Go back to the list page for the next item
            page.goto('https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283')
            page.wait_for_selector('tbody')
        
        browser.close()
        self.stdout.write(self.style.SUCCESS('Done.'))

    def generate_image(self, main):
        """Generate an image using Cloudflare AI API"""
        load_dotenv()
        account_id = os.getenv('CFACCOUNTID')
        api_token = os.getenv('CFAPITOKEN')
        gemini_api_key = os.getenv('GEMINI_API_KEY')

        if not account_id or not api_token:
            self.stderr.write(self.style.ERROR('Cloudflare credentials not found in environment variables.'))
            return

        if not gemini_api_key:
            self.stderr.write(self.style.ERROR('Gemini API key not found in environment variables.'))
            return

        # Step 1: Translate Korean to English using Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-3.5-flash')

        try:
            prompt = f"Translate this Korean food name to English. Return only the English translation, no additional text: {main}"
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
            self.stdout.write(self.style.SUCCESS(f"Translated: {main} -> {translated_text}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error translating text with Gemini: {str(e)}"))
            translated_text = main  # Fallback to original text

        # Step 2: Generate image using translated text
        imageurl = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        image_prompt = f"Create a picture of {translated_text} dish in a fancy restaurant"
        image_payload = {
            "prompt": image_prompt,
            "seed": random.randint(0, 1000000),
        }

        try:
            image_response = requests.post(imageurl, headers=headers, json=image_payload)

            if image_response.status_code == 200:
                with open(f"{main}.png", "wb") as f:
                    f.write(image_response.content)
                self.stdout.write(self.style.SUCCESS(f"Image saved as {main}.png"))
                self.upload_to_storage(f"{main}.png", f"{main}.png")
            else:
                self.stderr.write(self.style.ERROR(f"Image generation API error: {image_response.status_code} {image_response.text}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating image: {str(e)}"))

    def upload_to_storage(self, file_path, object_name):
        """Upload image to storage using PUT with PAR token"""
        load_dotenv()
        par_token = os.getenv('STORAGE_PAR_TOKEN')
        namespace = os.getenv('STORAGE_NAMESPACE', 'ax0ym4amgnfk')
        bucket = os.getenv('STORAGE_BUCKET', 'bucket-20260516-0145')

        # if not par_token:
        #     self.stderr.write(self.style.ERROR('Storage PAR token not found in environment variables.'))
        #     return

        # url = f"https://objectstorage.ap-chuncheon-1.oraclecloud.com/p/{par_token}/n/{namespace}/b/{bucket}/o/{object_name}"
        url = f"https://objectstorage.ap-chuncheon-1.oraclecloud.com/p/IB7TC1jkYnlu_awkWLKTY6GDr0_dXG5nEh1CAupBQjjIGAcCIbmn_4Gxma2GeE3U/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/{object_name}"

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                response = requests.put(url, data=file_data, timeout=10)

            if response.status_code in [200, 201]:
                self.stdout.write(self.style.SUCCESS(f'Successfully uploaded {file_path} to storage'))
            else:
                self.stderr.write(self.style.ERROR(f'Failed to upload: {response.status_code} {response.text}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error uploading to storage: {str(e)}'))
    
    def get_menu(self, img_path):
        load_dotenv()
        client = google_genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

        
        try:
            # Read image and convert to base64
            mime_type, _ = mimetypes.guess_type(img_path)
            if not mime_type:
                mime_type = "image/png"

            with open(img_path, 'rb') as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            # Gemini API call
            contents = [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_image,
                    },
                },
                {"text": "{'id': '낙지콩나물덮밥-ch-20260101-thu-breakfast', 'main': '낙지콩나물덮밥', 'side': '유부장국, 유린기 닭:브라질산, 중화품배추찜, 마카로니크래미샐러드, 고들빼기무침, 마시는 요구르트', 'enmain': 'Rice with octopus bean sprouts', 'ensub': 'Fried Tofu Soup, Yuringi Chicken: Brazilian, Chinese Cabbage Steamed, Macaroni Crami Salad, Seasoned Godeul, Drinking Yogurt', 'price': 8000, 'time': 'lunch', 'day': 'tue', 'place': 'cg', 'extra_menu': '', 'extra_price': 0, 'non_pork': False, 'storage_url': '/낙지콩나물덮밥.png'}처럼 각 메뉴를 정리해주세요. place는 청운관 학생식당: ch, 청운관 교직원식당: cg, 푸른솔 학생식당: ph, 푸른솔 교직원식당: pg, 학생회관 학생식당: hh, 학생회관 교직원식당: hg입니다. trailing comma가 없도록 해주세요. main에는 띄어쓰기가 없도록 해주세요. stamp는 금지 표시가 있으면 True, 없으면 False입니다. py list로 만들고 # 메모 없이 작성해주세요."},
            ]
            
            response = client.models.generate_content(model="gemini-3.5-flash", contents=contents)
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
    
            def _save_items(items):
                for menu in items:
                    MenuItem.objects.create(
                        id=str(uuid.uuid4()),
                        main=menu.get('main', ''),
                        side=menu.get('side', ''),
                        price=menu.get('price', 0),
                        meal=menu.get('time', ''),
                        day=menu.get('day', ''),
                        place=menu.get('place', ''),
                        extra='',
                        date=None,
                        stamp=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"Successfully posted item: {menu.get('main', 'Unknown Menu Item')}"))
                    self.generate_image(menu.get('main', ''))                    
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(_save_items, collection).result()
        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Error: {err}'))