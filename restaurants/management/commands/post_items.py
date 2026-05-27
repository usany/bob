from django.core.management.base import BaseCommand
from restaurants.models import MenuItem
import requests
import os
import random

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
        url = "https://objectstorage.ap-chuncheon-1.oraclecloud.com/p/IB7TC1jkYnlu_awkWLKTY6GDr0_dXG5nEh1CAupBQjjIGAcCIbmn_4Gxma2GeE3U/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/jgdinner"
        file_path = os.path.join('static', 'favicon.png')
        
        # Example data - customize as needed
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        count = options.get('count', 1)
        for i in range(count):
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    # Using a 10s timeout is good practice for network requests
                    response = requests.put(url, data=file_data, timeout=10)
                    
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
            self.style.SUCCESS('Successfully uploaded file to storage')
        )
        self.stdout.write(
            self.style.SUCCESS('Finished processing upload attempts.')
        )
