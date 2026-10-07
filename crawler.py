"""Scrape menu data from university websites using Playwright.

Usage:
    python crawler.py --source khu --campus seoul
    python crawler.py --source hufs --student
    python crawler.py --source dorm
"""
import argparse
import base64
import json
import logging
import mimetypes
import os
import pathlib
import random
import re

import requests
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

load_dotenv()

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    # api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    # base_url="https://integrate.api.nvidia.com/v1",
    # api_key=os.getenv("VERCELKEY"),
    # base_url="https://ai-gateway.vercel.sh/v1",
)

GEMINI_MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]

# Cloudflare D1 table previously managed by the Django `restaurants.MenuItem` model
MENU_TABLE = 'restaurants_menuitem'
MENU_FIELDS = ['main', 'side', 'enmain', 'enside', 'place', 'extra', 'enextra', 'date', 'day', 'meal', 'price', 'stamp']

DOWNLOAD_DIR = pathlib.Path(__file__).parent / 'downloads'


def d1_query(sql, params=None):
    """Run a SQL statement against Cloudflare D1 via the HTTP API"""
    account_id = os.getenv('CFACCOUNTID')
    database_id = os.getenv('CFDATABASEID')
    api_token = os.getenv('CFTOKEN')
    if not account_id or not database_id or not api_token:
        raise RuntimeError('Cloudflare D1 credentials (CFACCOUNTID, CFDATABASEID, CFTOKEN) not found in environment variables.')

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_token}"},
        json={"sql": sql, "params": params or []},
        timeout=30,
    )
    data = response.json()
    if not response.ok or not data.get('success'):
        raise RuntimeError(f"D1 query failed: {response.status_code} {data.get('errors')}")
    return data['result']


def save_menu_item(item_id, **fields):
    """Insert a menu item, or update every field if the id already exists"""
    fields['price'] = str(fields.get('price', ''))
    fields['stamp'] = 1 if fields.get('stamp') else 0
    columns = ['id'] + MENU_FIELDS
    sql = (
        f"INSERT INTO {MENU_TABLE} ({', '.join(columns)}) "
        f"VALUES ({', '.join('?' for _ in columns)}) "
        f"ON CONFLICT(id) DO UPDATE SET {', '.join(f'{c}=excluded.{c}' for c in MENU_FIELDS)}"
    )
    d1_query(sql, [item_id] + [fields.get(c, '') for c in MENU_FIELDS])


def run(source, campus=None, student=False):
    with sync_playwright() as p:
        if source == 'dorm':
            scrap_dorm(p)
        elif source == 'hufs':
            scrap_hufs(p, student)
        elif source == 'khu':
            if not campus:
                logger.error('Please specify --campus (seoul or global) for KHU')
                return
            scrap(p, campus == 'seoul')


def scrap_dorm(playwright):
    """Scrape dorm menu"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    logger.info('Navigating to the list page...')
    link = 'https://dorm2.khu.ac.kr/50/5030.do#'
    page.goto(link, timeout=60000)

    page.locator('a').filter(has_text='전체보기').first.click()
    page.wait_for_selector('td.te_left')
    raw_dates = page.locator('[id^="vDate"]').all_inner_texts()
    dates = [date.split('년', 1)[0].strip()+('0'+date.split('년', 1)[1].split('월', 1)[0].strip() if len(date.split('년', 1)[1].split('월', 1)[0].strip()) == 1 else date.split('년', 1)[1].split('월', 1)[0].strip())+('0'+date.split('월', 1)[1].split('일', 1)[0].strip() if len(date.split('월', 1)[1].split('일', 1)[0].strip()) == 1 else date.split('월', 1)[1].split('일', 1)[0].strip()) for date in raw_dates]
    menu_texts = page.locator('td.te_left').all_inner_texts()
    logger.info(str(menu_texts))
    logger.info(f'Found {len(menu_texts)} items')

    browser.close()

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
    translated = translate_text(all_texts) if all_texts else []
    trans_map = {all_texts[i]: translated[i] for i in range(len(all_texts))} if len(translated) == len(all_texts) else {}

    # Second pass: create/update menu items using cached translations
    for index, menu in enumerate(menu_texts):
        if menu == '미운영':
            continue
        day = 'mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri'
        day_index = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 7}[day]
        date = dates[day_index]
        if menu.startswith('A코너 : '):
            first_part = menu.split(' : ', 1)[1]
            first_menu = first_part.split(',', 1) if not first_part.startswith('미운영') else ''
            second_menu = menu.split('B코너 : ', 1)[1].strip().split(',', 1)
            corners = [
                (first_menu[0].strip() if first_menu else '',
                 first_menu[1].split('B코너 : ', 1)[0].strip() if len(first_menu) > 1 else ''),
                (second_menu[0].strip() if second_menu else '',
                 second_menu[1].strip() if len(second_menu) > 1 else ''),
            ]
            meal = 'lunch'
        else:
            menu_parts = menu.split(',', 1)
            corners = [(menu_parts[0].strip() if menu_parts else '',
                        menu_parts[1].strip() if len(menu_parts) > 1 else '')]
            meal = 'breakfast' if index % 3 == 0 else ('lunch' if index % 3 == 1 else 'dinner')

        for main, side in corners:
            if not main:
                continue
            enmain = trans_map.get(main, main)
            save_menu_item(
                main+'-'+place+'-'+date+'-'+day+'-'+meal,
                main=main,
                side=side,
                enmain=enmain,
                enside=trans_map.get(side, side),
                day=day,
                meal=meal,
                place=place,
                price='5500',
                extra='',
                enextra='',
                date=date,
                stamp=False,
            )
            generate_image(main, enmain)


def scrap_hufs(playwright, is_student):
    """Scrape HUFS menu"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    logger.info('Navigating to the list page...')
    link = 'https://www.hufs.ac.kr/hufs/11318/subview.do#click'
    page.goto(link, timeout=60000)
    if not is_student:
        page.locator('a').filter(has_text='교수회관식당').click()
    page.wait_for_selector('td.no-menu, td.menu')
    date_elements = page.locator('[id^="date_"]').all()
    dates = [elem.get_attribute('id').replace('date_', '').replace('-', '') for elem in date_elements]
    menu_texts = page.locator('td.no-menu, td.menu').all_inner_texts()
    logger.info(str(menu_texts))
    logger.info(f'Found {len(menu_texts)} items')

    browser.close()

    def parse(index, menu):
        if menu.startswith('등록된') or menu.startswith('방학중에는') or index % 7 < 1 or index % 7 > 5:
            return None
        menu_parts = menu.split('\n')
        main = menu_parts[0].strip().replace(':', '') if menu_parts else ''
        side = ' '.join(menu_parts[1:-4]) if len(menu_parts) > 1 else ''
        if not main:
            return None
        return menu_parts, main, side

    # First pass: collect all Korean texts to translate in one batch
    all_texts = []
    for index, menu in enumerate(menu_texts):
        parsed = parse(index, menu)
        if not parsed:
            continue
        _, main, side = parsed
        all_texts.append(main)
        if side:
            all_texts.append(side)

    # Batch translate all texts at once
    translated = translate_text(all_texts) if all_texts else []
    trans_map = {all_texts[i]: translated[i] for i in range(len(all_texts))} if len(translated) == len(all_texts) else {}

    # Second pass: create/update menu items using cached translations
    for index, menu in enumerate(menu_texts):
        parsed = parse(index, menu)
        if not parsed:
            continue
        menu_parts, main, side = parsed
        place = 'his' if is_student else 'hgs'
        meal = 'lunch' if not is_student else 'breakfast' if index < 7 else 'lunch' if index < 28 else 'dinner'
        day = 'mon' if index % 7 == 1 else 'tue' if index % 7 == 2 else 'wed' if index % 7 == 3 else 'thu' if index % 7 == 4 else 'fri'
        day_index = {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6}[day]
        date = dates[day_index] if day_index < len(dates) else ''
        enmain = trans_map.get(main, main)
        save_menu_item(
            main+'-'+place+'-'+date+'-'+day+'-'+meal,
            main=main,
            side=side,
            enmain=enmain,
            enside=trans_map.get(side, side),
            day=day,
            meal=meal,
            place=place,
            price=menu_parts[-1].split('(')[0].replace(',', '').replace('원', '').strip(),
            extra='',
            enextra='',
            date=date,
            stamp=False,
        )
        generate_image(main, enmain)


def scrap(playwright, is_seoul=True):
    """Scrape KHU menu and download images"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    logger.info('Navigating to the list page...')
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

    logger.info(f'Found {len(raw_links)} links in tbody.')

    DOWNLOAD_DIR.mkdir(exist_ok=True)

    for link_data in raw_links:
        if not link_data['href'] or link_data['href'].startswith('javascript:'):
            logger.info(f'Handling link: {link_data["text"]}')

            if page.url != link:
                page.goto(link, timeout=60000)
                page.wait_for_selector('tbody')

            try:
                with page.expect_navigation(wait_until='domcontentloaded'):
                    page.locator('tbody a').filter(has_text=link_data['text']).first.click()
            except Exception as err:
                logger.error(f'Failed to navigate to {link_data["text"]}: {err}')
                continue
        else:
            logger.info(f'Visiting URL: {link_data["href"]}')
            try:
                page.goto(link_data['href'], wait_until='domcontentloaded')
            except Exception as err:
                logger.error(f'Failed to visit {link_data["href"]}: {err}')
                continue

        title = page.locator('p.txt06').first.inner_text().strip()

        # Find PNG/JPG images
        images = page.locator('img').all()
        image_urls = []
        for img in images:
            src = img.get_attribute('src')
            if src and src.endswith(('.png', '.jpg')) and 'decoGnb' not in src and 'footLogo' not in src and 'ico' not in src:
                image_urls.append(src)
        logger.info(f'Found {len(image_urls)} images on this page.')

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

                local_path = DOWNLOAD_DIR / image_name

                response = page.request.get(absolute_img_url)
                if response.status == 200:
                    local_path.write_bytes(response.body())
                    logger.info(f'Downloaded: {image_name}')
                    get_menu(str(local_path), title)
            except Exception as err:
                logger.error(f'Failed to download image {img_url}: {err}')

        # Go back to the list page for the next item
        page.goto('https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283', timeout=60000)
        page.wait_for_selector('tbody')

    browser.close()
    logger.info('Done.')


def translate_text(texts):
    """Translate Korean text(s) to English using Gemini

    Args:
        texts: A single string or list of strings to translate

    Returns:
        A single translated string or list of translated strings (matching input type)
    """
    if not os.getenv('GEMINI_API_KEY'):
        logger.error('Gemini API key not found in environment variables.')
        return texts

    # Handle single string input
    is_single = isinstance(texts, str)
    text_list = [texts] if is_single else [t for t in texts if t]

    # Create prompt for batch translation
    text_items = '\n'.join([f'{i+1}. {text}' for i, text in enumerate(text_list)])
    prompt = f"""Translate the following Korean texts to English. Return ONLY the translations in the same order, one per line, with no numbers or extra text:

{text_items}"""

    for model in GEMINI_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            translations = response.choices[0].message.content.strip().split('\n')

            for ko, en in zip(text_list, translations):
                logger.info(f'  {ko} -> {en}')

            # Return in the same format as input
            if is_single:
                return translations[0] if translations else texts
            if len(translations) == len(text_list):
                return translations
            logger.warning(f"Model {model} returned {len(translations)} translations for {len(text_list)} texts. Trying next...")
            logger.warning(f"translations: {translations}")
            logger.warning(f"text_list: {text_list}")
        except Exception as e:
            logger.error(f"Model {model} failed: {e}. Trying next...")

    logger.error("All Gemini models failed for translation.")
    return texts


def generate_image(main, enmain):
    """Generate an image using Cloudflare AI API"""
    account_id = os.getenv('CFACCOUNTID')
    api_token = os.getenv('CFAPITOKEN')

    if not account_id or not api_token:
        logger.error('Cloudflare credentials not found in environment variables.')
        return

    logger.info(f'{main}\t{enmain}')

    imageurl = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    image_payload = {
        "prompt": f"Create a picture of simple {enmain} dish in a fancy restaurant",
        "seed": random.randint(0, 1000000),
    }

    # Sanitize filename: remove characters invalid on Windows
    safe_main = re.sub(r'[\\/*?"<>|]', '+', main)
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    image_path = DOWNLOAD_DIR / f"{safe_main}.png"

    try:
        image_response = requests.post(imageurl, headers=headers, json=image_payload)

        if image_response.status_code == 200:
            image_path.write_bytes(image_response.content)
            logger.info(f"Image saved as {image_path}")
            upload_to_storage(image_path, safe_main)
        else:
            logger.error(f"Image generation API error: {image_response.status_code} {image_response.text}")
    except Exception as e:
        logger.error(f"Error generating image: {e}")


def upload_to_storage(file_path, object_name):
    """Upload image to storage using PUT with PAR token"""
    url = f"{os.getenv('STORAGE_URL')}{object_name}"

    if not os.path.exists(file_path):
        logger.error(f'File not found: {file_path}')
        return

    try:
        with open(file_path, 'rb') as f:
            response = requests.put(url, data=f.read(), timeout=10)

        if response.status_code in [200, 201]:
            logger.info(f'Successfully uploaded {file_path} to storage')
        else:
            logger.error(f'Failed to upload: {response.status_code} {response.text}')
    except Exception as e:
        logger.error(f'Error uploading to storage: {e}')


def get_menu(img_path, title=""):
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

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}},
                ]
            }
        ]

        for model in GEMINI_MODELS:
            try:
                response = client.chat.completions.create(model=model, messages=messages)
            except Exception as model_err:
                logger.error(f"Model {model} failed: {model_err}. Trying next...")
                continue

            logger.info(f'Gemini response: {model} {response.choices[0].message.content}')

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

            for menu in collection:
                save_menu_item(menu.get('id', ''), **{field: menu.get(field, '') for field in MENU_FIELDS if field != 'stamp'}, stamp=menu.get('stamp', False))
                logger.info(f"Successfully posted item: {menu.get('main', 'Unknown Menu Item')}")
                generate_image(menu.get('main', ''), menu.get('enmain', menu.get('main', '')))
            break  # success — no need to try next model
        else:
            logger.error("All Gemini models failed for get_menu.")

    except Exception as err:
        logger.error(f'Error: {err}')


def main():
    parser = argparse.ArgumentParser(description='Scrape menu data from university websites using Playwright')
    parser.add_argument('--source', required=True, choices=['khu', 'hufs', 'dorm'], help='Source to scrape: khu, hufs, or dorm')
    parser.add_argument('--campus', choices=['seoul', 'global'], help='Campus for KHU: seoul or global')
    parser.add_argument('--student', action='store_true', help='Use student menu for HUFS')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    run(args.source, args.campus, args.student)


if __name__ == '__main__':
    main()
