import os
from utils.config import Config


SYS_CONFIG = Config(
    os.path.join(os.path.dirname(__file__), "config", "config.yaml")
)

ALERT_KEYS = {
    "alert_id": str,
    "failure_count": int
}

FTC_METRICS = {
    "monitor_ftc_login": {
        "method": "check_ftc_login",
        "description": "Check Login Status"
    }
}

METRICS_CLASSES = {
    "FTC_LOGIN": "metrics.ftc.FtcMonitor"
}

SCREEN_CAP_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <title>Title of the document</title>
  </head>
  <body>
    <div>
      <img src="data:image/png;base64,{png_b64}"/>
    </div>
  </body>
</html>
"""

IMG_URL_TEMPLATE = "http://{ip}/monitor/logs/screencap/{id}"
