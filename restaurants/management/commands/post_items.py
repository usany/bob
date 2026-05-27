from django.core.management.base import BaseCommand
from restaurants.models import MenuItem
from django.utils import timezone
import random
import requests
import os

class Command(BaseCommand):
    help = 'Post items to the storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of items to post',
        )

    def handle(self, *args, **options):
        count = options['count']
        url = "https://objectstorage.ap-chuncheon-1.oraclecloud.com/p/IB7TC1jkYnlu_awkWLKTY6GDr0_dXG5nEh1CAupBQjjIGAcCIbmn_4Gxma2GeE3U/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/jgdinner"
        file_path = os.path.join('static', 'favicon.png')
        
        # Example data - customize as needed
        sample_titles = ['Special Dish', 'Daily Special', 'Chef Recommendation', 'Seasonal Menu']
        sample_mains = ['Rice', 'Noodles', 'Soup', 'Salad']
        sample_sides = ['Kimchi', 'Pickles', 'Vegetables', 'Tofu']
        sample_times = ['30 min', '45 min', '1 hour', '20 min']
        sample_places = ['Main Hall', 'Private Room', 'Outdoor', 'Counter']
        sample_extras = ['Spicy', 'Mild', 'Sweet', 'Savory']
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        for i in range(count):
            item = MenuItem.objects.create(
                title=f"{random.choice(sample_titles)} {i+1}",
                storage_url=f'/menu/item-{i+1}',
                order=MenuItem.objects.count() + 1,
                main=random.choice(sample_mains),
                side=random.choice(sample_sides),
                time=random.choice(sample_times),
                place=random.choice(sample_places),
                extra_menu=random.choice(sample_extras),
                price=random.randint(10000, 50000),
                non_pork=random.choice([True, False])
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully posted item: {item.title}')
            )
        
            try:
                with open(file_path, 'rb') as f:
                    # Using a 10s timeout is good practice for network requests
                    response = requests.put(url, data=f, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        self.stdout.write(
                            self.style.SUCCESS(f'Successfully uploaded {file_path} to storage (Attempt {i+1})')
                        )
                    else:
                        self.stderr.write(
                            self.style.ERROR(f'Failed to upload: {response.status_code} {response.text}')
                        )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))

        self.stdout.write(
            self.style.SUCCESS(f'Successfully posted {count} items to database')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Finished processing {count} upload attempts.')
        )
