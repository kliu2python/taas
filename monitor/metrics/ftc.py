import monitor.alert as alert
import monitor.constants as constants
from utils.metrics import Metrics


class FTC:
    @classmethod
    def check_ftc_login(cls):
        alert_type = "FTC_LOGIN"
        disable_alert = constants.SYS_CONFIG.metrics.get(
            alert_type, {}
        ).get("disable_alert", False)
        should_create = alert.should_alert(alert_type)
        if should_create:
            if not disable_alert:
                alert.create(alert_type)
            return 0
        should_close = alert.should_stop_alert(alert_type)
        if should_close:
            if not disable_alert:
                alert.close(alert_type)
        return 1


class FtcMonitor(Metrics):
    def __init__(self):
        super().__init__(
            constants.FTC_METRICS,
            "FTC_PROD",
            FTC,
            config_path=constants.SYS_CONFIG
        )
