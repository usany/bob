"""Run the Playwright scrapers on a cron schedule.

Usage:
    python scheduler.py
"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import crawler

logger = logging.getLogger(__name__)

TIMEZONE = 'Asia/Seoul'
DAY_OF_WEEK = 'fri'
HOUR = 23
START_MINUTE = 5

# (job id, crawler.run kwargs) — each job runs 5 minutes after the previous one
JOBS = [
    ('playwright_khu_seoul', {'source': 'khu', 'campus': 'seoul'}),
    ('playwright_khu_global', {'source': 'khu', 'campus': 'global'}),
    ('playwright_hufs_student', {'source': 'hufs', 'student': True}),
    ('playwright_hufs_staff', {'source': 'hufs', 'student': False}),
    ('playwright_dorm', {'source': 'dorm'}),
]


def run_job(job_id, kwargs):
    logger.info(f'Starting {job_id}')
    try:
        crawler.run(**kwargs)
        logger.info(f'Finished {job_id}')
    except Exception:
        logger.exception(f'{job_id} failed')


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # A single worker queues jobs so Playwright runs one at a time even if triggers overlap
    scheduler = BlockingScheduler(
        timezone=TIMEZONE,
        executors={'default': {'type': 'threadpool', 'max_workers': 1}},
        job_defaults={'coalesce': True, 'misfire_grace_time': 3600},
    )

    for offset, (job_id, kwargs) in enumerate(JOBS):
        scheduler.add_job(
            run_job,
            CronTrigger(day_of_week=DAY_OF_WEEK, hour=HOUR, minute=START_MINUTE + offset * 5, timezone=TIMEZONE),
            args=[job_id, kwargs],
            id=job_id,
            replace_existing=True,
        )

    logger.info('Scheduler started. Waiting for jobs...')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutting down scheduler...')


if __name__ == '__main__':
    main()
