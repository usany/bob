from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
import os

# Create scheduler
scheduler = BackgroundScheduler()

def start():
    """Start the scheduler with scheduled jobs"""
    
    # Clear expired sessions daily at 3 AM
    scheduler.add_job(
        call_command,
        'cron',
        args=['clearsessions'],
        id='clear_sessions',
        hour=3,
        minute=0,
        replace_existing=True
    )
    
    # Post items to database every day at 10 AM
    scheduler.add_job(
        call_command,
        'cron',
        args=['post_items', '--count', '5'],
        id='post_items',
        hour=10,
        minute=0,
        replace_existing=True
    )
    
    # Add more jobs here as needed
    # Example: Run custom command every hour
    # scheduler.add_job(
    #     call_command,
    #     'cron',
    #     args=['your_hourly_task'],
    #     id='hourly_task',
    #     hour='*',
    #     minute=0,
    #     replace_existing=True
    # )
    
    # Example: Run backup daily at 2 AM
    # scheduler.add_job(
    #     call_command,
    #     'cron',
    #     args=['backup'],
    #     id='daily_backup',
    #     hour=2,
    #     minute=0,
    #     replace_existing=True
    # )
    
    scheduler.start()

def stop():
    """Stop the scheduler"""
    scheduler.shutdown()
