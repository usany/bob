from django.core.management.base import BaseCommand
import requests
import os

        url = "https://objectstorage.ap-chuncheon-1.oraclecloud.com/p/IB7TC1jkYnlu_awkWLKTY6GDr0_dXG5nEh1CAupBQjjIGAcCIbmn_4Gxma2GeE3U/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/jgdinner"
        file_path = os.path.join('static', 'favicon.png')
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        for i in range(count):
            try:
                with open(file_path, 'rb') as f:
                    # Using a 10s timeout is good practice for network requests
                    response = requests.put(url, data=f, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        self.stdout.write(
                            self.style.SUCCESS(f'Successfully uploaded {file_path} to storage (Attempt {i+1})')
                        )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))

        self.stdout.write(
            self.style.SUCCESS(f'Finished processing {count} upload attempts.')
        )
