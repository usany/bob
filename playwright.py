from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
import os
import pathlib
from restaurants.models import MenuItem
import random
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import requests
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    # api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    # base_url="https://integrate.api.nvidia.com/v1",
    # api_key=os.getenv("VERCELKEY"),
    # base_url="https://ai-gateway.vercel.sh/v1",
)
import mimetypes
import base64
import re
import json
import uuid

class Command(BaseCommand):
    help = 'Scrape menu data from university websites using Playwright'
    
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
        page.goto(link, timeout=60000)
        
        page.locator('a').filter(has_text='전체보기').first.click()
        page.wait_for_selector('td.te_left')
        raw_dates = page.locator('[id^="vDate"]').all_inner_texts()
        dates = [date.split('년', 1)[0].strip()+('0'+date.split('년', 1)[1].split('월', 1)[0].strip() if len(date.split('년', 1)[1].split('월', 1)[0].strip()) == 1 else date.split('년', 1)[1].split('월', 1)[0].strip())+('0'+date.split('월', 1)[1].split('일', 1)[0].strip() if len(date.split('월', 1)[1].split('일', 1)[0].strip()) == 1 else date.split('월', 1)[1].split('일', 1)[0].strip()) for date in raw_dates]
        menu_texts = page.locator('td.te_left').all_inner_texts()
        self.stdout.write(str(menu_texts))
        self.stdout.write(f'Found {len(menu_texts)} items')
        
        browser.close()
        
        # Create MenuItem objects outside of Playwright context
        def create_menu_items():
            place = 'jg'
            # First pass: collect all Korean texts to translate in one batch
            all_texts = []
            for index, menu in enumerate(menu_texts):
                if menu == '미운영':
                    continue
                if menu.startswith('A코너 : '):
                    first_part = menu.split(' : ', 1)[1]
                    first_menu = first_part.split(',', 1) if not first_part.startswith('미운영') else ''
                    main = first_menu[0].strip() if first_menu else ''
                    side = first_menu[1].split('B코너 : ', 1)[0].strip() if len(first_menu) > 1 else ''
                    all_texts.append(main)
                    if side:
                        all_texts.append(side)
                    second_part = menu.split('B코너 : ', 1)[1].strip()
                    second_menu = second_part.split(',', 1)
                    main2 = second_menu[0].strip() if second_menu else ''
                    side2 = second_menu[1].strip() if len(second_menu) > 1 else ''
                    all_texts.append(main2)
                    if side2:
                        all_texts.append(side2)
                else:
                    menu_parts = menu.split(',', 1)
                    main = menu_parts[0].strip() if menu_parts else ''
                    side = menu_parts[1].strip() if len(menu_parts) > 1 else ''
                    all_texts.append(main)
                    if side:
                        all_texts.append(side)

            # Batch translate all texts at once
            translated = self.translate_text(all_texts) if all_texts else []
            trans_map = {all_texts[i]: translated[i] for i in range(len(all_texts))} if len(translated) == len(all_texts) else {}

            # Second pass: create/update menu items using cached translations
            for index, menu in enumerate(menu_texts):
                if menu == '미운영':
                    continue
                if menu.startswith('A코너 : '):
                    first_part = menu.split(' : ', 1)[1]
                    first_menu = first_part.split(',', 1) if not first_part.startswith('미운영') else ''
                    main = first_menu[0].strip() if first_menu else ''
                    side = first_menu[1].split('B코너 : ', 1)[0].strip() if len(first_menu) > 1 else ''
                    day = 'mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri'
                    day_index = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 7}[day]
                    date = dates[day_index]
                    enmain = trans_map.get(main, main)
                    enside = trans_map.get(side, side)
                    item_id = main+'-'+place+'-'+date+'-'+day+'-lunch'
                    defaults_dict = dict(
                        main=main,
                        side=side,
                        enmain=enmain,
                        enside=enside,
                        day=day,
                        meal='lunch',
                        place=place,
                        price='5500',
                        extra='',
                        enextra='',
                        date=date,
                        stamp=False,
                    )
                    if main:
                        obj, created = MenuItem.objects.get_or_create(id=item_id, defaults=defaults_dict)
                        if not created:
                            MenuItem.objects.filter(id=item_id).update(**defaults_dict)
                    
                    self.generate_image(main, enmain) if main else None

                    second_part = menu.split('B코너 : ', 1)[1].strip()
                    second_menu = second_part.split(',', 1)
                    main = second_menu[0].strip() if second_menu else ''
                    side = second_menu[1].strip() if len(second_menu) > 1 else ''
                    enmain = trans_map.get(main, main)
                    enside = trans_map.get(side, side)
                    item_id2 = main+'-'+place+'-'+date+'-'+day+'-lunch'
                    defaults_dict2 = dict(
                        main=main,
                        side=side,
                        enmain=enmain,
                        enside=enside,
                        day=day,
                        meal='lunch',
                        place=place,
                        price='5500',
                        extra='',
                        enextra='',
                        date=date,
                        stamp=False,
                    )
                    if main:
                        obj, created = MenuItem.objects.get_or_create(id=item_id2, defaults=defaults_dict2)
                        if not created:
                            MenuItem.objects.filter(id=item_id2).update(**defaults_dict2)
                    self.generate_image(main, enmain) if main else None

                else:
                    menu_parts = menu.split(',', 1)
                    main = menu_parts[0].strip() if menu_parts else ''
                    side = menu_parts[1].strip() if len(menu_parts) > 1 else ''
                    meal = 'breakfast' if index % 3 == 0 else ('lunch' if index % 3 == 1 else 'dinner')
                    day = 'mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri'
                    day_index = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 7}[day]
                    date = dates[day_index]
                    enmain = trans_map.get(main, main)
                    enside = trans_map.get(side, side)
                    item_id3 = main+'-'+place+'-'+date+'-'+day+'-'+meal
                    defaults_dict3 = dict(
                        main=main,
                        side=side,
                        enmain=enmain,
                        enside=enside,
                        day=day,
                        meal=meal,
                        place=place,
                        price='5500',
                        extra='',
                        enextra='',
                        date=date,
                        stamp=False,
                    )
                    if main:
                        obj, created = MenuItem.objects.get_or_create(id=item_id3, defaults=defaults_dict3)
                        if not created:
                            MenuItem.objects.filter(id=item_id3).update(**defaults_dict3)
                    self.generate_image(main, enmain) if main else None

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
        page.goto(link, timeout=60000)
        if not is_student:
            page.locator('a').filter(has_text='교수회관식당').click()
            # page.wait_for_selector('td.no-menu, td.menu')
        page.wait_for_selector('td.no-menu, td.menu')
        date_elements = page.locator('[id^="date_"]').all()
        days = [elem.inner_text().split('(')[1].split(')')[0] for elem in date_elements if '(' in elem.inner_text()]
        dates = [elem.get_attribute('id').replace('date_', '').replace('-', '') for elem in date_elements]
        day_date_map = {day: date for day, date in zip(days, dates)}
        menu_texts = page.locator('td.no-menu, td.menu').all_inner_texts()
        self.stdout.write(str(menu_texts))
        self.stdout.write(f'Found {len(menu_texts)} items')

        browser.close()

        # Create MenuItem objects outside of Playwright context
        def create_menu_items():
            # First pass: collect all Korean texts to translate in one batch
            all_texts = []
            for index, menu in enumerate(menu_texts):
                if menu.startswith('등록된') or menu.startswith('방학중에는') or index % 7 < 1 or index % 7 > 5:
                    continue
                menu_parts = menu.split('\n')
                main = menu_parts[0].strip().replace(':', '') if menu_parts else ''
                side = ' '.join(menu_parts[1:-4]) if len(menu_parts) > 1 else ''
                if not main:
                    continue
                all_texts.append(main)
                if side:
                    all_texts.append(side)

            # Batch translate all texts at once
            translated = self.translate_text(all_texts) if all_texts else []
            trans_map = {all_texts[i]: translated[i] for i in range(len(all_texts))} if len(translated) == len(all_texts) else {}

            # Second pass: create/update menu items using cached translations
            for index, menu in enumerate(menu_texts):
                if menu.startswith('등록된') or menu.startswith('방학중에는') or index % 7 < 1 or index % 7 > 5:
                    continue
                menu_parts = menu.split('\n')
                main = menu_parts[0].strip().replace(':', '') if menu_parts else ''
                side = ' '.join(menu_parts[1:-4]) if len(menu_parts) > 1 else ''
                if not main:
                    continue
                place = 'his' if is_student else 'hgs'
                meal = 'lunch' if not is_student else 'breakfast' if index < 7 else 'lunch' if index < 28 else 'dinner'
                day = 'mon' if index % 7 == 1 else 'tue' if index % 7 == 2 else 'wed' if index % 7 == 3 else 'thu' if index % 7 == 4 else 'fri'
                day_index = {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6}[day]
                date = dates[day_index] if day_index < len(dates) else ''
                item_id = main+'-'+place+'-'+date+'-'+day+'-'+meal
                enmain = trans_map.get(main, main)
                enside = trans_map.get(side, side)
                defaults_dict4 = dict(
                    main=main,
                    side=side,
                    enmain=enmain,
                    enside=enside,
                    day=day,
                    meal=meal,
                    place=place,
                    price=menu_parts[-1].split('(')[0].replace(',', '').replace('원', '').strip(),
                    extra='',
                    enextra='',
                    date=date,
                    stamp=False,
                )
                obj, created = MenuItem.objects.get_or_create(id=item_id, defaults=defaults_dict4)
                if not created:
                    MenuItem.objects.filter(id=item_id).update(**defaults_dict4)
                self.generate_image(main, enmain)

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
        
        page.goto(link, timeout=60000)
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
                    page.goto(link, timeout=60000)
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
                if src and src.endswith('.png') and 'decoGnb' not in src and 'footLogo' not in src and 'ico' not in src:                    image_urls.append(src)
                elif src and src.endswith('.jpg') and 'decoGnb' not in src and 'footLogo' not in src and 'ico' not in src:                    image_urls.append(src)
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
                        self.get_menu(str(local_path), title)
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f'Failed to download image {img_url}: {str(err)}'))
            
            # Go back to the list page for the next item
            page.goto('https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283', timeout=60000)
            page.wait_for_selector('tbody')
        
        browser.close()
        self.stdout.write(self.style.SUCCESS('Done.'))

    
    def translate_text(self, texts):
        """Translate Korean text(s) to English using Gemini
        
        Args:
            texts: A single string or list of strings to translate
            
        Returns:
            A single translated string or list of translated strings (matching input type)
        """
        load_dotenv()
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not gemini_api_key:
            self.stderr.write(self.style.ERROR('Gemini API key not found in environment variables.'))
            return texts
        
        # Handle single string input
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else [t for t in texts if t]
        
        # Create prompt for batch translation
        text_items = '\n'.join([f'{i+1}. {text}' for i, text in enumerate(text_list)])
        prompt = f"""Translate the following Korean texts to English. Return ONLY the translations in the same order, one per line, with no numbers or extra text:

{text_items}"""

        for model in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro",None]:
            if model is None:
                self.stderr.write(self.style.ERROR("All Gemini models failed for translation."))
                return texts
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                translations = response.choices[0].message.content.strip().split('\n')

                for ko, en in zip(text_list, translations):
                    self.stdout.write(f'  {ko} -> {en}')

                # Return in the same format as input
                if is_single:
                    return translations[0] if translations else texts
                else:
                    if len(translations) == len(text_list):
                        return translations
                    else:
                        # self.stdout.write(translations)
                        # self.stdout.write(text_list)
                        self.stderr.write(self.style.WARNING(f"Model {model} returned {len(translations)} translations for {len(text_list)} texts. Trying next..."))
                        self.stderr.write(self.style.WARNING(f"translations: {translations}"))
                        self.stderr.write(self.style.WARNING(f"text_list: {text_list}"))
                        continue

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Model {model} failed: {str(e)}. Trying next..."))
                continue

    def generate_image(self, main, enmain):
        """Generate an image using Cloudflare AI API"""
        load_dotenv()
        account_id = os.getenv('CFACCOUNTID')
        api_token = os.getenv('CFAPITOKEN')

        if not account_id or not api_token:
            self.stderr.write(self.style.ERROR('Cloudflare credentials not found in environment variables.'))
            return

        self.stdout.write(f'{main}\t{enmain}')
        # Step 1: Use the English dish name directly
        translated_text = enmain

        # Step 2: Generate image using translated text
        imageurl = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        image_prompt = f"Create a picture of simple {translated_text} dish in a fancy restaurant"
        image_payload = {
            "prompt": image_prompt,
            "seed": random.randint(0, 1000000),
        }

        # Sanitize filename: remove characters invalid on Windows
        safe_main = re.sub(r'[\\/*?"<>|]', '+', main)

        try:
            image_response = requests.post(imageurl, headers=headers, json=image_payload)

            if image_response.status_code == 200:
                with open(f"{safe_main}.png", "wb") as f:
                    f.write(image_response.content)
                self.stdout.write(self.style.SUCCESS(f"Image saved as {safe_main}.png"))
                self.upload_to_storage(f"{safe_main}.png", f"{safe_main}")
            else:
                self.stderr.write(self.style.ERROR(f"Image generation API error: {image_response.status_code} {image_response.text}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error generating image: {str(e)}"))

    def upload_to_storage(self, file_path, object_name):
        """Upload image to storage using PUT with PAR token"""
        load_dotenv()
        par_token = os.getenv('STORAGE_PAR_TOKEN')
        namespace = os.getenv('STORAGE_NAMESPACE', 'ax0ym4amgnfk')
        storage_url = os.getenv('STORAGE_URL')

        url = f"{storage_url}{object_name}"

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
    
    def get_menu(self, img_path, title=""):
        load_dotenv()

        
        try:
            # Read image and convert to base64
            mime_type, _ = mimetypes.guess_type(img_path)
            if not mime_type:
                mime_type = "image/png"

            with open(img_path, 'rb') as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
            
            if '청운관' in title:
                place_instruction = "place는 학생식당은 ch, 교직원식당은 cg입니다. 단품, 든든, 우아, 푸짐은 모두 lunch입니다. 간편식, 간식은 정리하지 않고 넘어가주세요."
            elif '푸른솔' in title:
                place_instruction = "place는 학생식당은 ph, 교직원식당은 pg입니다. 조식은 breakfast입니다. OneDishSETSelf-Bar, 한소반SETSelf-Bar, 면가득은 모두 lunch입니다. dinner는 없습니다. TO-GO가 포함된 메뉴는 정리하지 않고 넘어가주세요."
            elif '학생회관' in title:
                place_instruction = "place는 학생식당은 hh, 교직원식당은 hg입니다. 포케, 컵밥은 서로 다른 breakfast 메뉴입니다. 단품, 든든, 우아, 푸짐은 모두 lunch입니다. dinner 메뉴는 학생식당과 교직원식당이 같은 메뉴입니다."
            else:
                place_instruction = "place는 jg입니다. 점심의 T/O(6,500원) 메뉴만 정리해주세요. main이 오늘의샐러드인 경우 enmain은 Salad of the Day로 작성해주세요."
            prompt_text = f"{{'id': '낙지콩나물덮밥-ch-20260101-thu-breakfast', 'main': '낙지콩나물덮밥', 'side': '유부장국, 유린기 닭:브라질산, 중화품배추찜, 마카로니크래미샐러드, 고들빼기무침, 마시는 요구르트', 'enmain': 'Rice with octopus bean sprouts', 'enside': 'Fried Tofu Soup, Yuringi Chicken: Brazilian, Chinese Cabbage Steamed, Macaroni Crami Salad, Seasoned Godeul, Drinking Yogurt', 'price': 8000, 'date': '20260101', 'day': 'tue', 'meal': 'lunch', 'place': 'cg', 'extra': '일식돈가스 추가시 8000', 'enextra': 'additional Japanese-style pork cutlet 8000', 'stamp': False }}처럼 각 메뉴를 정리해주세요. {place_instruction} trailing comma가 없도록 해주세요. id는 main-place-date-day-meal 순서로 합쳐서 / 기호를 쓰지 않게 만들어주세요. main에는 띄어쓰기가 없도록 해주세요. 추가 메뉴가 없는 경우 extra와 enextra는 ''입니다. date는 표 상단의 날짜와 제목인 {title}를 참고해서 yyyymmdd 형식으로 작성해주세요. stamp는 금지 표시가 있으면 True, 없으면 False입니다. stamp의 대문자에 유의해주세요. JSON이 아닌 py list로 만들고 # 메모 없이 작성해주세요."

            # Gemini API call
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            for model in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro",None]:
                if model is None:
                    self.stderr.write(self.style.ERROR("All Gemini models failed for get_menu."))
                    break
                try:
                    response = client.chat.completions.create(model=model, messages=messages)
                except Exception as model_err:
                    self.stderr.write(self.style.ERROR(f"Model {model} failed: {str(model_err)}. Trying next..."))
                    continue

                self.stdout.write(f'Gemini response: {model} {response.choices[0].message.content}')

                # Strip markdown code fences if present, then parse into a list
                raw = response.choices[0].message.content.strip()
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
                        item_id5 = menu.get('id', '')
                        defaults_dict5 = dict(
                            main=menu.get('main', ''),
                            side=menu.get('side', ''),
                            enmain=menu.get('enmain', ''),
                            enside=menu.get('enside', ''),
                            price=menu.get('price', ''),
                            meal=menu.get('meal', ''),
                            day=menu.get('day', ''),
                            place=menu.get('place', ''),
                            extra=menu.get('extra', ''),
                            enextra=menu.get('enextra', ''),
                            date=menu.get('date', ''),
                            stamp=menu.get('stamp', False),
                        )
                        obj, created = MenuItem.objects.get_or_create(id=item_id5, defaults=defaults_dict5)
                        if not created:
                            MenuItem.objects.filter(id=item_id5).update(**defaults_dict5)
                        self.stdout.write(self.style.SUCCESS(f"Successfully posted item: {menu.get('main', 'Unknown Menu Item')}"))
                        self.generate_image(menu.get('main', ''), menu.get('enmain', menu.get('main', '')))
                with ThreadPoolExecutor(max_workers=1) as executor:
                    executor.submit(_save_items, collection).result()
                break  # success — no need to try next model

        except Exception as err:
            self.stderr.write(self.style.ERROR(f'Error: {err}'))