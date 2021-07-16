import monitor.logs as logs_handler
from flask import jsonify, make_response, render_template_string
from flask_restful import Resource, request
from monitor.constants import SCREEN_CAP_HTML
from monitor.datastore import alert_datastore
from utils.logger import get_logger
from rest import RestApi

rest = RestApi(base_route="/monitor/")
logger = get_logger()


@rest.route("metrics/update")
class UpdateMertics(Resource):
    """
    post data example:
    {
        "alert_type": "FTC_LOGIN",
        "value": 0, 1 or others
        "operation": set/incr
        "logs": [{
            "create_at": xxx,
            "message": xxxx,
            "screencap": xxxxx b64png
        }]
    }
    """
    def post(self):
        try:
            op_data = request.json
            action = op_data.get("operation")
            if action:
                op = getattr(alert_datastore, action)
                op(
                    "failure_count",
                    op_data.get("value"),
                    op_data.get("alert_type")
                )
            logs_handler.add_log(op_data)
            return jsonify({"results": "SUCCESS"})
        except Exception as e:
            logger.exception("Error when do update metrics post", exc_info=e)
            return f"Fail, {e}", 400


@rest.route("logs/screencap/<string:img_id>")
class ShowScreenCapture(Resource):
    def get(self, img_id):
        try:
            png_b64 = logs_handler.get_screen_cap(img_id)
            html = SCREEN_CAP_HTML.format(png_b64=png_b64)
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template_string(html), 200, headers)
        except Exception as e:
            logger.exception("Error when get screen cap", exc_info=e)
            return f"Fail, {e}", 400
