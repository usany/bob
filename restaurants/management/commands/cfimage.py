from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
import os
import pathlib
from restaurants.models import MenuItem
import random
from concurrent.futures import ThreadPoolExecutor

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
                        main=main,
                        side=side,
                        price=6500,
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        time='lunch',
                        place=place,
                        extra_menu='',
                        extra_price=None,
                        non_pork=False,
                        storage_url='https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/'+place+'lunch',
                    )
                    second_part = first_menu[1].split('B코너 : ', 1)[1].strip() if len(first_menu) > 1 else ''
                    second_menu = second_part.split(',', 1)
                    main = second_menu[0].strip() if second_menu else ''
                    side = second_menu[1].strip() if len(second_menu) > 1 else ''
                    MenuItem.objects.create(
                        main=main,
                        side=side,
                        price=5500,
                        time='lunch',
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        place=place,
                        extra_menu='',
                        extra_price=None,
                        non_pork=False,
                        storage_url='https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/'+place+'lunch',
                    )
                else:
                    menu_parts = menu.split(',', 1)
                    main = menu_parts[0].strip() if menu_parts else ''
                    side = menu_parts[1].strip() if len(menu_parts) > 1 else ''
                    time = 'breakfast' if index % 3 == 0 else 'dinner'
                    MenuItem.objects.create(
                        main=main,
                        side=side,
                        price=5500,
                        time=time,
                        day='mon' if index < 3 else 'tue' if index < 6 else 'wed' if index < 9 else 'thu' if index < 12 else 'fri',
                        place=place,
                        extra_menu='',
                        extra_price=None,
                        non_pork=False,
                        storage_url='https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/'+place+time,
                    )
        
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
                time = 'lunch' if not is_student else 'breakfast' if index < 7 else 'lunch' if index < 28 else 'dinner'
                MenuItem.objects.create(
                    main=main,
                    side=side,
                    price=int(menu_parts[-1].split('(')[0].replace(',', '').replace('원', '')),
                    time=time,
                    day='mon' if index % 7 == 1 else 'tue' if index % 7 == 2 else 'wed' if index % 7 == 3 else 'thu' if index % 7 == 4 else 'fri',
                    place=place,
                    extra_menu='',
                    extra_price=None,
                    non_pork=False,
                    storage_url='https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/'+place+time,
                )

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
                except Exception as err:
                    self.stdout.write(self.style.ERROR(f'Failed to download image {img_url}: {str(err)}'))
            
            # Go back to the list page for the next item
            page.goto('https://www.khu.ac.kr/kor/user/bbs/BMSR00040/list.do?menuNo=200283')
            page.wait_for_selector('tbody')
        
        browser.close()
        self.stdout.write(self.style.SUCCESS('Done.'))
