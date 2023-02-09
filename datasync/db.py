# pylint: disable=too-few-public-methods,too-many-arguments
from datetime import datetime

from utils.db import Database
from utils.logger import get_logger

LOGGER = get_logger()


class FaccldCustomerDB(Database):
    def get_instances_info(self, accounts):
        accounts = [f'"{account}"' for account in accounts]
        query = (f"SELECT customers.user_email, facs.status, facs.domain_name, "
                 f"facs.region FROM facs join customers on facs.customer_id = "
                 f"customers.id where customers.user_email "
                 f"in ({','.join(accounts)})")
        info = self.query_auto_connect(query=query)
        return info

    def get_total_instance_count(self):
        query = "SELECT COUNT(*) FROM faccloud.facs"
        count = self.query_auto_connect(query=query)
        return count[0].get("COUNT(*)")


class FaccldCeleryDB(Database):
    def update_instance_check_schedule(self, minute, hour):
        query = (f"update "
                 f"celery_crontab_schedule "
                 f"join "
                 f"celery_periodic_task "
                 f"on "
                 f"celery_crontab_schedule.id=celery_periodic_task.crontab_id "
                 f"set "
                 f"celery_crontab_schedule.minute={minute}, "
                 f"celery_crontab_schedule.hour={hour} "
                 f"where "
                 f"celery_periodic_task.name = 'task_dr_instance_daily_check'")
        self.query_auto_connect(query=query)

        curr_time = datetime.strftime(datetime.utcnow(), "%Y-%m-%d %H:%M:%S")
        query = (
            f"update "
            f"celery_periodic_task_changed "
            f"set "
            f"last_update='{curr_time}'"
            f"where "
            f"id = 1"
        )
        self.query_auto_connect(query=query)
