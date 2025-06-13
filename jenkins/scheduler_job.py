import time

from apscheduler.schedulers.background import BackgroundScheduler
from jenkins.manager import JenkinsJobs
from utils.logger import get_logger

LOGGER = get_logger()


def job_task():
    """Fetch and store the Jenkins job structure."""
    JenkinsJobs().fetch_and_store_job_structure()


# Scheduler Setup for Background Task
def start_scheduler():
    """Set up the scheduler to periodically fetch and store job structure."""

    LOGGER.info("creating the scheduler job")
    scheduler = BackgroundScheduler()
    # Schedule the job to run every hour
    scheduler.add_job(job_task, 'interval', hours=24)
    scheduler.start()
    LOGGER.info("Scheduler started to update Jenkins job structure.")

    try:
        # Keep the scheduler running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


# Example usage:
if __name__ == "__main__":
    start_scheduler()
