"""
Restful API process
"""
import ssl

import eventlet

from utils.logger import get_logger

logger = get_logger("clear")
requests = eventlet.import_patched("requests")


class LoginError(Exception):
    pass


class ExecutionError(Exception):
    def __init__(self, message, err):
        self.msg = f"{message}\n Error: {err}"
        super().__init__(self.msg)

    def __str__(self):
        return self.msg


class BpClient:
    def __new__(cls, host, user, password, api_version=2):
        if api_version == 2:
            return BpClientV2(host, user, password)
        return BpClientV1(host, user, password)


class BpClientBase:
    adapter = requests.adapters.HTTPAdapter()
    adapter.init_poolmanager(
        connections=requests.adapters.DEFAULT_POOLSIZE,
        maxsize=requests.adapters.DEFAULT_POOLSIZE,
        block=requests.adapters.DEFAULT_POOLBLOCK,
        ssl_version=ssl.PROTOCOL_TLS
    )
    session_cache = {}

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.session_id = None
        self.session = requests.Session()
        self.run_id = None
        self.session.mount('https://', self.adapter)
        self._base_url = f"https://{self.host}/api/v1/bps"
        self.login_status = False

    # connect to the system
    def connect(self):
        resp = self.session.post(
            url=f"https://{self.host}/bps/api/v1/auth/session",
            json={'username': self.user, 'password': self.password},
            headers={'content-type': 'application/json'}, verify=False)
        if resp.status_code == 200:
            self.session_id = resp.json().get('sessionId')
            sess_id = resp.json().get('sessionId')
            api_key = resp.json().get('apiKey')
            self.session.headers['sessionId'] = sess_id
            self.session.headers['X-API-KEY'] = api_key
            self.session_cache[sess_id] = api_key
            logger.info(
                f"Successfully connected to {self.host}, "
                f"session_id={self.session_id}"
            )
        else:
            logger.error(
                f"Failed connecting to {self.host}: "
                f"{resp.status_code}, {resp.content}"
            )

    def _clear_all_sessions(self):
        self.adapter.close()
        for sess_id, api_key in self.session_cache.items():
            resp = requests.delete(
                f"https://{self.host}/api/v1/auth/session",
                verify=False,
                headers={
                    "sessionId": sess_id,
                    "X-API-KEY": api_key
                }
            )
            if resp.status_code == 204:
                logger.info(f"Session cleared for {sess_id},api_key: {api_key}")

    # disconnect from the systemWW
    def disconnect(self):
        resp = self.session.delete(
            url=f"https://{self.host}/api/v1/auth/session",
            verify=False
        )

        if resp.status_code == 204:
            self.session_id = None
            if 'sessionId' in self.session.headers:
                del self.session.headers['sessionId']
                del self.session.headers['X-API-KEY']
            logger.info(f"Successfully disconnected from {self.host}")
            self.session.close()
            self.login_status = False
        else:
            if self.login_status:
                logger.error(
                    f"Failed disconnecting from {self.host}: "
                    f"ret_code={resp.status_code}, content={resp.content}"
                )

    def _get(self, url, **kwargs):
        retry = 3
        resp = None
        while retry > 0:
            retry_login = kwargs.pop("retry_login", False)
            resp = self.session.get(
                url=f"{self._base_url}/{url}",
                verify=False,
                **kwargs
            )
            if resp.status_code < 400:
                break
            logger.warning(
                f"get to {url} with {kwargs} failed, retrying..({retry})"
            )
            if retry_login:
                try:
                    self.logout()
                    self.login()
                except Exception as e:
                    logger.info(f"Error when logout/login {e}")
            retry -= 1
        return resp

    # post from data model
    def _post(self, url, **kwargs):
        retry = 3
        resp = None
        while retry > 0:
            retry_login = kwargs.pop("retry_login", False)
            resp = self.session.post(
                url=f"{self._base_url}/{url}",
                headers={'content-type': 'application/json'},
                verify=False,
                **kwargs
            )
            if resp.status_code < 400:
                break
            logger.warning(
                f"post to {url} with {kwargs} failed, retrying..({retry})"
            )
            if retry_login:
                try:
                    self.logout()
                    self.login()
                except Exception as e:
                    logger.info(f"Error when logout/login {e}")
            retry -= 1
        return resp

    # Patch from data model
    def _patch(self, path, **kwargs):
        resp = self.session.patch(
            url=f"{self._base_url}/{path}",
            headers={'content-type': 'application/json'},
            verify=False,
            **kwargs
        )
        return resp

    # Put from data model
    def _put(self, path, **kwargs):
        resp = self.session.put(
            url=f"{self._base_url}/{path}",
            headers={'content-type': 'application/json'},
            verify=False,
            **kwargs
        )
        return resp

    # DELETE from data model
    def _delete(self, path):
        resp = self.session.put(
            url=f"{self._base_url}/{path}",
            headers={'content-type': 'application/json'},
            verify=False
        )
        return resp

    def login(self):
        raise NotImplementedError

    def logout(self):
        raise NotImplementedError

    def run_case(self, case_name, group):
        raise NotImplementedError

    def stop_run(self, run_id):
        raise NotImplementedError

    def get_report(
            self,
            file_path,
            run_id,
            report_format,
            section_ids=None,
            timeout=600):
        raise NotImplementedError

    def get_running_status(
            self,
            run_id,
            rts_group="summary",
            seconds=-1,
            data_points=1,
            for_print=True
    ):
        raise NotImplementedError

    def reserve_port(self, slot, ports, group, force):
        raise NotImplementedError

    def unreserve_port(self, slot, port_list, group, force):
        raise NotImplementedError


class BpClientV2(BpClientBase):
    def __init__(self, host, user, password):
        super().__init__(host, user, password)
        self._base_url = f"https://{self.host}/bps/api/v2/core"

    # login into the bps system
    def login(self):
        if self.session_id:
            self.logout()
        self.connect()
        resp = self._post(
            url='auth/login',
            json={
                'username': self.user,
                'password': self.password,
                'sessionId': self.session_id
            }
        )

        if resp.status_code == 200:
            logger.info(
                f"Login successful, user: {self.user} "
                f"session id is {self.session_id}"
            )
            self.login_status = True
        else:
            self.disconnect()
            raise LoginError(
                f"Failed to login with user: {self.user}, {resp.status_code}"
            )

    # logout from the bps system
    def logout(self):
        if self.run_id:
            try:
                self.stop_run(run_id=self.run_id)
            except Exception:
                pass
        if self.session_id:
            r = self._post(
                url='auth/logout',
                json={
                    'username': self.user,
                    'password': self.password,
                    'sessionId': self.session_id
                }
            )

            if r.status_code == 200:
                logger.info(f"Logout successful for user: {self.user} "
                            f"sessionid: {self.session_id}")
                self.disconnect()
            else:
                if self.login_status:
                    logger.error(
                        f"Logout failed: {r.status_code}, {r.content}"
                    )
        else:
            logger.info("Not logged in BP, skip logout")

    def run_case(self, case_name, group):
        resp = self._post(
            "testmodel/operations/run",
            json={
                "modelname": case_name,
                "group": group,
                "allowMalware": True
            }
        )
        data = resp.json()
        err = data.get("error")
        if err:
            raise ExecutionError(
                f"Error when run case {case_name}, group: {group}", err
            )
        self.run_id = data.get("runid")
        return self.run_id

    def stop_run(self, run_id):
        resp = self._post(
            "testmodel/operations/stopRun",
            json={
                'runid': run_id
            },
            timeout=60
        )
        if resp.status_code != 200:
            logger.error(
                f"Error when stop run id {run_id}, {resp.json().get('error')}"
            )

    def get_report(
            self,
            file_path,
            run_id,
            report_format,
            section_ids="",
            timeout=600
    ):
        def _get_report_url():
            return self._post(
                "reports/operations/exportReport",
                json=json,
                stream=True,
                timeout=timeout,
                retry_login=True
            )

        def _download_report():
            return self.session.get(
                url=url, verify=False, headers={
                    "content-type": "application/json"
                }
            )

        json = {
            "filepath": file_path,
            "runid": run_id,
            "reportType": report_format,
            "sectionIds": section_ids,
            "dataType": "ALL"
        }
        resp = _get_report_url()
        if resp.status_code != 200:
            logger.error("Failed to get report url")
            return

        url = f"https://{self.host}{resp.text}"
        resp = _download_report()
        if resp.status_code == 200:
            with open(file_path, "wb") as F:
                for chunk in resp.iter_content(chunk_size=1024):
                    F.write(chunk)
            resp.close()
            return file_path
        logger.error(
            f"Error when get report for {run_id},{resp.json().get('error')}"
        )

    def reserve_port(self, slot, ports, group, force=True):
        for port in ports:
            resp = self._post(
                "topology/operations/reserve",
                json={"reservation": [{
                    "slot": slot,
                    "port": port,
                    "group": group,
                    "force": force
                }]
                }
            )
            if resp.status_code == 204:
                logger.info(f"Ports already reserved: slot: {slot}, {port}")
                continue
            if resp.status_code != 200:
                raise ExecutionError(
                    f"Error when reserve slot: {slot}, port: {port}",
                    resp.json().get("error")
                )

    def unreserve_port(self, slot, port_list, group, force=True):
        resp = self._post(
            "topology/operations/unreserve",
            json={
                "slot": slot,
                "portList": port_list,
                "group": group,
                "force": force
            }
        )
        if resp.status_code != 200:
            raise ExecutionError(
                f"Error when unreserve port",
                resp.json().get("error")
            )

    def get_running_status(
            self,
            run_id,
            rts_group="summary",
            seconds=-1,
            data_points=1,
            for_print=True
    ):
        resp = eventlet.with_timeout(
            3,
            self._post,
            "testmodel/operations/realTimeStats",
            json={
                'runid': run_id,
                'rtsgroup': rts_group,
                'numSeconds': seconds,
                'numDataPoints': data_points
            },
            timeout_value="Timeout for getting running status"
        )
        if isinstance(resp, str):
            return resp
        if resp.status_code == 200:
            return resp.json()
        return resp.json().get("error")


class BpClientV1(BpClientBase):
    # login into the bps system
    def login(self):
        if self.session_id:
            self.logout()
        self.connect()

    # logout from the bps system
    def logout(self):
        if self.run_id:
            try:
                self.stop_run(run_id=self.run_id)
            except Exception:
                pass
        self.disconnect()

    def run_case(self, case_name, group):
        resp = self._post(
            "tests/operations/start",
            json={
                "modelname": case_name,
                "group": group
            }
        )
        data = resp.json()
        err = data.get("error")
        if err:
            raise ExecutionError(
                f"Error when run case {case_name}, group: {group}", err
            )
        self.run_id = data.get("testid")
        return self.run_id

    def stop_run(self, run_id):
        resp = self._post(
            "tests/operations/stop",
            json={
                'testid': run_id
            },
            timeout=60
        )
        if resp.status_code != 200:
            logger.error(
                f"Error when stop run id {run_id}, {resp.json().get('error')}"
            )

    def get_report(
            self,
            file_path,
            run_id,
            report_format,
            section_ids=None,
            timeout=600):
        def _get_report():
            return self._get(
                f"export/report/{run_id}/{report_format}",
                stream=True,
                timeout=timeout,
                retry_login=True
            )

        logger.info(f"v1 api client not support section_id: {section_ids}")
        resp = _get_report()
        if resp.status_code != 200:
            if report_format not in ["csv"]:
                report_format = "csv"
                resp = _get_report()
        if resp.status_code == 200:
            with open(file_path, "wb") as F:
                for chunk in resp.iter_content(chunk_size=1024):
                    F.write(chunk)
            resp.close()
            return file_path
        logger.error(
            f"Error when get report for {run_id},{resp.json().get('error')}"
        )

    def reserve_port(self, slot, ports, group, force=True):
        resp = self._post(
            "ports/operations/reserve",
            json={
                "slot": slot,
                "portList": ports,
                "group": group,
                "force": force
            }
        )
        if resp.status_code != 200:
            raise ExecutionError(
                f"Error when reserve slot: {slot}, port list: {ports}",
                resp.json().get("error")
            )

    def unreserve_port(self, slot, port_list, group, force=True):
        resp = self._post(
            "ports/operations/unreserve",
            json={
                "slot": slot,
                "portList": port_list,
                "group": group,
                "force": force
            }
        )
        if resp.status_code != 200:
            raise ExecutionError(
                f"Error when unreserve port",
                resp.json().get("error")
            )

    def get_running_status(
            self,
            run_id,
            rts_group="summary",
            seconds=-1,
            data_points=1,
            for_print=True
    ):
        resp = eventlet.with_timeout(
            3,
            self._post,
            "tests/operations/getRealTimeStatistics",
            json={
                'runid': run_id
            },
            timeout_value="Timeout for getting running status"
        )
        if isinstance(resp, str):
            return resp
        if resp.status_code == 200:
            return resp.json().get("rts")
        return resp.json().get("error")


if __name__ == '__main__':
    import time

    bp = BpClient("10.160.1.101", "vNP-bmrkauto", "a", 2)
    bp.login()
    try:
        run_id = bp.run_case("VM32-BMRK-DPDK-IPV4-HTTP64K-FW", 1)
        i = 0
        while i < 30:
            i += 1
            print(bp.get_running_status(run_id))
            time.sleep(5)
    except Exception as e:
        logger.exception("", exc_info=e)
    bp.logout()
