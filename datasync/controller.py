import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from time import sleep

import pika
import pika.exceptions as pika_ex

import datasync.constants as constants
from datasync.caches import TaskCache
from datasync.conf import CONF
from datasync.db import FaccldCeleryDB
from datasync.db import FaccldCustomerDB
from utils.logger import get_logger

LOGGER = get_logger()


class Amqp:
    def __init__(self, url_name, queues):
        con_url = CONF.get(url_name)
        if not con_url:
            raise Exception("qmqp connection url must be specified")
        self.queues = queues
        self.channel = None
        self.con_url = con_url
        self.connect()

    def connect(self):
        if (
                not self.channel
                or self.channel.is_closed
                or self.channel.connection.is_closed
        ):
            conn = pika.BlockingConnection(pika.URLParameters(self.con_url))
            self.channel = conn.channel()
            self.channel.confirm_delivery()
            self.channel.basic_qos(prefetch_count=1)
            for queue in self.queues:
                try:
                    self.channel.queue_declare(queue.value)
                except pika.exceptions.StreamLostError:
                    pass

    def publish(self, queue, msg):
        self.connect()
        if isinstance(msg, dict):
            msg = json.dumps(msg).encode()
        for i, _ in enumerate(range(3)):
            try:
                self.channel.basic_publish("", queue, msg)
                break
            except Exception as ex:
                if not self.channel.is_closed:
                    self.close()
                self.connect()
                if i == 2:
                    raise ex
                LOGGER.info("failed to publish, retrying")

    def receive(self, queue, timeout=600):
        self.connect()
        method_frame, properties, body = next(self.channel.consume(
            queue, inactivity_timeout=timeout
        ))
        if method_frame:
            self.channel.basic_ack(method_frame.delivery_tag)
            return body

    def cancel(self):
        self.connect()
        self.channel.cancel()

    def clear_queue(self, queue):
        self.connect()
        self.channel.queue_purge(queue)

    def close(self):
        if self.channel:
            self.channel.close()
            self.channel = None


class AccountManager:
    def __init__(self):
        self.ready_accounts = self.get_accounts()
        self.fail_accounts = {}
        self.acct_failures = defaultdict(int)
        self.db = FaccldCustomerDB(**CONF["db"]["customer_db"])
        self.update_domain_names(self.ready_accounts)
        self.check_accounts()

    @staticmethod
    def get_accounts():
        accounts = {}
        accounts_list = CONF.get("accounts")
        for account in accounts_list:
            LOGGER.info(f"Register FC Account: {account}")
            accounts[account["forticare_un"]] = account
        return accounts

    def deactive_account(self, username):
        if username in self.ready_accounts:
            LOGGER.info(f"Deactivating account: {username}")
            self.fail_accounts[username] = self.ready_accounts.pop(username)

    def active_account(self, username):
        if username in self.fail_accounts:
            LOGGER.info(f"Activating account: {username}")
            self.ready_accounts[username] = self.fail_accounts.pop(username)

    def drop_account(self, username):
        if username in self.fail_accounts:
            LOGGER.warning(f"Dropping Account: {username}")
            self.fail_accounts.pop(username)

    def update_domain_names(self, accounts):
        domain_names = {}
        instances = self.db.get_instances_info(accounts)
        for instance in instances:
            domain_names[instance["user_email"]] = instance["domain_name"]
        for acct in self.ready_accounts.keys():
            self.ready_accounts[acct]["custom_data"]["fac_ip"] = (
                domain_names[acct]
            )

    def do_check_accounts(self, accounts):
        if accounts:
            status = defaultdict(int)
            instances = self.db.get_instances_info(accounts)
            for inst in instances:
                if inst["status"] == 2:
                    status[inst["user_email"]] += 1

            for acct, stat in status.items():
                if stat == 2:
                    self.active_account(acct)
                else:
                    self.deactive_account(acct)

    def check_accounts(self):
        self.do_check_accounts(self.ready_accounts)
        self.do_check_accounts(self.fail_accounts)

    def wait_data_sync(self, unit_wait_time=300, reboot_count=8, ready=False):
        LOGGER.info("Waiting data restore complete")
        elapsed = 0
        rebooted = set()
        total_instances = self.db.get_total_instance_count()
        timeout = total_instances/reboot_count * unit_wait_time
        while elapsed < timeout:
            instances = self.db.get_instances_info(self.ready_accounts)
            for inst in instances:
                if inst["region"] in ["dr"]:
                    if inst["status"] != 2:
                        rebooted.add(inst["domain_name"])
            if ready:
                if len(rebooted) == 0:
                    return True
            else:
                if len(rebooted) == len(self.ready_accounts):
                    return True
            sleep(10)
        else:
            if rebooted:
                LOGGER.warning("Not all accounts rebooted")
                return False
            raise Exception(f"no facs rebooted in {timeout} seconds")

    def check_drop_accounts(self):
        for acct in self.fail_accounts.keys():
            self.acct_failures[acct] += 1
            if self.acct_failures[acct] > 3:
                self.drop_account(acct)

    def wait_account_ready(self, timeout=300):
        LOGGER.info("Waiting account ready")
        curr_time = 0
        while curr_time < timeout:
            self.check_accounts()
            if len(self.fail_accounts) == 0:
                break
            curr_time += 10
            sleep(10)

        self.check_drop_accounts()


class Controller:
    def __init__(self):
        self.task_queue = Amqp("amqp_runner", constants.TASKQueues)
        self.push_queue = Amqp("amqp_pushproxy", constants.PUSHPROXYQueues)
        self.am = AccountManager()
        self.celery_db = FaccldCeleryDB(**CONF["db"]["celery_db"])
        self.celery_timedelta = CONF.get("celery_time_delta", 1)
        self.cache = TaskCache()
        self.ref_user = ""

    def update_reference_user(self):
        appendx = datetime.strftime(datetime.now(), "%m-%d-%Y_%H-%M-%S")
        self.ref_user = f"ref_{appendx}"
        LOGGER.info(f"Using User: {self.ref_user}")

    def push_controller_data(self, category, value):
        data = {
            "job": "datasync_mtbf",
            "time": float(datetime.now().timestamp()),
            "timeout": CONF.get("sync_timeout", 60) * 60,
            "data": [{
                "category": category,
                "description": "ftid",
                "labels": [{"module": "controller"}],
                "values": [float(value)]
            }]
        }
        data = json.dumps(data).encode()
        self.push_queue.publish(
            constants.PUSHPROXYQueues.PUSHPROXY_GATEWAY.value, data
        )

    def purge_all_queues(self):
        for queue in constants.TASKQueues:
            try:
                self.task_queue.clear_queue(queue.value)
            except pika.exceptions.StreamLostError:
                pass

    def dispatch_job(self, job_list, queue):
        LOGGER.info(f"Dispatching job to queue: {queue}")
        self.am.wait_account_ready()
        success = 0
        for job in job_list:
            for _ in range(3):
                try:
                    job["target_un"] = self.ref_user
                    self.task_queue.publish(queue, job)
                    success += 1
                    break
                except (pika_ex.UnroutableError, pika_ex.NackError):
                    LOGGER.info("failed to publish, retrying")
        self.task_queue.close()
        if success == 0:
            raise Exception(f"Failed to dispatch job to queue: {queue}")

    def push_sync_totals(self):
        self.push_controller_data(
            constants.PROMETHEUS_DATA_SYNC_CLIENT_SUCCESS,
            self.cache.get("sync_success_clients", default=0)
        ),
        self.push_controller_data(
            constants.PROMETHEUS_DATA_SYNC_CLIENT_FAIL,
            self.cache.get("sync_failed_clients", default=0)
        )

    def waiting_job(self, queue, timeout=300):
        LOGGER.info("Waiting remote job done")
        start_time = datetime.now()
        replies = 0
        while (datetime.now() - start_time).seconds < timeout:
            msg = self.task_queue.receive(queue)
            if msg:
                replies += 1
                msg = json.loads(msg.decode())
                results = msg.pop("results", [])
                for result in results:
                    res = result["data"][0]
                    if res["category"] in [
                        constants.PROMETHEUS_DATA_SYNC
                    ]:
                        if res["values"] == float(1):
                            self.cache.incr(
                                "sync_success_clients", 1
                            )
                        else:
                            self.cache.incr(
                                "sync_failed_clients", 1
                            )
                    result = json.dumps(result).encode()
                    self.push_queue.publish(
                        constants.PUSHPROXYQueues.PUSHPROXY_GATEWAY.value,
                        result
                    )
            else:
                break

            if replies == len(self.am.ready_accounts):
                self.task_queue.cancel()
                break
            sleep(10)
        self.push_queue.close()
        self.task_queue.close()

    def check_sync(self):
        value = 0
        ex = None
        try:
            result = self.am.wait_data_sync()
            if result:
                value = 1
        except Exception as e:
            ex = e
        finally:
            if value == 1:
                category = constants.PROMETHEUS_DATA_SYNC_TASKS_SUCCESS
                key = "sync_success_tasks"
            else:
                category = constants.PROMETHEUS_DATA_SYNC_TASKS_FAIL
                key = "sync_fail_tasks"
            self.cache.incr(key, 1)
            value = self.cache.get(key)
            self.push_controller_data(category, value)
            if ex:
                raise ex

    def update_cron_tab(self):
        dt = datetime.utcnow()
        minutes = self.celery_timedelta
        if dt.second > 57:
            minutes += 1
        dt = dt + timedelta(minutes=minutes)
        LOGGER.info(f"updating cron job to mins = {dt.minute}, hrs = {dt.hour}")
        self.celery_db.update_instance_check_schedule(
            minute=dt.minute, hour=dt.hour
        )

    def check_run_pause(self):
        while True:
            if self.cache.get("running", 0) == 1:
                break
            sleep(5)

    def update_cycle_number(self):
        self.cache.incr("sync_task_cycles", 1)
        cycles = self.cache.get("sync_task_cycles")
        self.push_controller_data(
            constants.PROMETHEUS_DATA_SYNC_CYCLES, cycles
        )
        LOGGER.info(f"---Round: {cycles}---")

    def run(self):
        self.purge_all_queues()
        self.check_run_pause()
        self.update_cycle_number()

        self.am.wait_account_ready()
        self.am.wait_data_sync(ready=True)

        ready_accounts = list(self.am.ready_accounts.values())
        self.update_reference_user()
        self.dispatch_job(
            ready_accounts, constants.TASKQueues.DATASYNC_TASK_MAIN.value
        )
        self.waiting_job(
            constants.TASKQueues.DATASYNC_TASK_MAIN_REPLY.value
        )
        
        self.update_cron_tab()
        self.check_sync()
        self.am.wait_account_ready()

        self.dispatch_job(
            ready_accounts, constants.TASKQueues.DATASYNC_TASK_DR.value
        )
        self.waiting_job(
            constants.TASKQueues.DATASYNC_TASK_DR_REPLY.value,
        )
        self.push_sync_totals()


def serve():
    controller = Controller()
    while True:
        try:
            controller.run()
        except Exception as e:
            LOGGER.error("Error when run", exc_info=e)
            sleep(10)


if __name__ == "__main__":
    serve()
