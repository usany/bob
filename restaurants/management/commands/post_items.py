from django.core.management.base import BaseCommand
from restaurants.models import MenuItem
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Post items to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of items to post',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Example data - customize as needed
        sample_titles = ['Special Dish', 'Daily Special', 'Chef Recommendation', 'Seasonal Menu']
        sample_mains = ['Rice', 'Noodles', 'Soup', 'Salad']
        sample_sides = ['Kimchi', 'Pickles', 'Vegetables', 'Tofu']
        sample_times = ['30 min', '45 min', '1 hour', '20 min']
        sample_places = ['Main Hall', 'Private Room', 'Outdoor', 'Counter']
        sample_extras = ['Spicy', 'Mild', 'Sweet', 'Savory']
        
        for i in range(count):
            item = MenuItem.objects.create(
                title=f"{random.choice(sample_titles)} {i+1}",
                url=f'/menu/item-{i+1}',
                order=MenuItem.objects.count() + 1,
                main=random.choice(sample_mains),
                side=random.choice(sample_sides),
                time=random.choice(sample_times),
                place=random.choice(sample_places),
                extra=random.choice(sample_extras),
                price=random.randint(10000, 50000),
                pork=random.choice([True, False])
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully posted item: {item.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully posted {count} items to database')
        )
