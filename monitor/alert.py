from time import sleep

import opsgenie_sdk

from monitor.constants import SYS_CONFIG
from monitor.datastore import alert_datastore
from utils.logger import get_logger

logger = get_logger()
genie_conf = opsgenie_sdk.configuration.Configuration()
genie_conf.api_key["Authorization"] = (
    SYS_CONFIG.alert_system.get("opsgenie").get("api_key")
)
api_client = opsgenie_sdk.api_client.ApiClient(configuration=genie_conf)
alert_api = opsgenie_sdk.AlertApi(api_client=api_client)


def _get_request_status(request_id):
    retry = 10
    err = None
    while retry > 0:
        try:
            resp = alert_api.get_request_status(request_id=request_id)
            return resp
        except opsgenie_sdk.ApiException as err:
            retry -= 1
            sleep(3)
    if err:
        logger.exception("Error when get request status", exc_info=err)


def should_alert(alert_type):
    def translate_compare(a, b, opt):
        if a > b and opt in ["gt"]:
            ret = True
        elif a >= b and opt in ["ge"]:
            ret = True
        elif a < b and opt in ["lt"]:
            ret = True
        elif a <= b and opt in ["le"]:
            ret = True
        else:
            ret = False
        return ret

    cfg = SYS_CONFIG.metrics.get(alert_type)
    compare = cfg.get("compare")
    thres_hold = cfg.get("thres_hold")
    alert_freq = cfg.get("alert_freq")
    alert_id = alert_datastore.get("alert_id", alert_type, None)
    if alert_id:
        if alert_freq in ["once"]:
            return False
    failures = alert_datastore.get("failure_count", alert_type, 0)
    return translate_compare(failures, thres_hold, compare)


def should_stop_alert(alert_type):
    alert_id = alert_datastore.get("alert_id", alert_type, None)
    failures = alert_datastore.get("failure_count", alert_type, 0)
    if alert_id and failures == 0:
        return True
    return False


def create_(alert_type):
    logger.info("Alert created")
    alert_datastore.set("alert_id", "alert_id", alert_type)


def close_(alert_type):
    logger.info("Alert Closed")
    alert_datastore.delete("alert_id", alert_type)
    alert_datastore.set("failure_count", 0, alert_type)


def create(alert_type):
    """
    Create a alert to opsgenie example usage from opsgenine website

    body = opsgenie_sdk.CreateAlertPayload(
        message="Test - Test of ftc login checker",
        source="FTC Login Checker",
        alias="ftc_login_monitor",
        description="Login Failure!",
        responders=[{
            "name": "sunnyvale-maas-infra",
            "type": "team"
        }],
        visible_to=[
            {"name": "sunnyvale-maas-infra",
             "type": "team"}],
        details={"Product": "FAS",
                 "Type": "Test"},
        entity="An example entity",
        priority="P1"
    )
    """
    try:
        data = SYS_CONFIG.metrics.get(alert_type).get(
            "alert_payload")
        body = opsgenie_sdk.CreateAlertPayload(**data)
        create_response = alert_api.create_alert(create_alert_payload=body)
        alert_datastore.set("alert_id", "alert_id", alert_type)
        logger.info(create_response)
        request_id = create_response.request_id
        request_status = _get_request_status(request_id)
        logger.info(request_status)
        alert_id = request_status.data.alert_id
        alert_datastore.set("alert_id", alert_id, alert_type)
    except Exception as err:
        logger.exception("Exception when create_alert", exc_info=err)


def close(alert_type):
    body = opsgenie_sdk.CloseAlertPayload(
        note="problem gone", source="ftc login checker"
    )
    try:
        logger.info(f"closing alert for {alert_type}")
        alert_id = alert_datastore.get("alert_id", alert_type)
        close_response = alert_api.close_alert(
            identifier=alert_id, close_alert_payload=body
        )
        logger.info(close_response)
        alert_datastore.delete("alert_id", alert_type)
        alert_datastore.set("failure_count", 0, alert_type)
        return close_response
    except Exception as err:
        logger.exception("Exception when close alert", exc_info=err)


if __name__ == "__main__":
    query = 'source=ftc-login-checker'
    alerts = alert_api.list_alerts(
        sort='updatedAt',
        order='asc',
        search_identifier_type='name',
        query=query
    )
    for alias in alerts.data:
        delete_response = alert_api.delete_alert(
            identifier=alias.alias,
            identifier_type="id",
        )
        logger.info(delete_response)
