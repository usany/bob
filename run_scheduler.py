import signal
import sys
from django.core.management.base import BaseCommand
from restaurants.scheduler import start, stop


class Command(BaseCommand):
    help = 'Start the APScheduler and keep the process alive'

    def handle(self, *args, **options):
        def sigterm_handler(signum, frame):
            self.stdout.write('Received SIGTERM, shutting down scheduler...')
            stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGINT, sigterm_handler)

        start()
        self.stdout.write(self.style.SUCCESS('Scheduler started. Waiting for jobs...'))

        import time
        while True:
            time.sleep(1)
