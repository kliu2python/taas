import qrdisplay.qr as qr
from flask import jsonify
from flask_restful import Resource, request
from rest import RestApi
from utils.logger import get_logger

rest = RestApi(base_route="/qrdisplay/")
logger = get_logger()
_reserve_id = None


@rest.route("display")
class QrDisplay(Resource):
    def post(self):
        """
        post data example:
        {
            "reserve_id": "xxxx"
            "image": BASE64 image string
        }
        return:
        {"results": "SUCCESS"} : Display success
        """
        try:
            data = request.json
            ret = qr.show_qrcode(**data)
            return jsonify({"results": ret})
        except Exception as e:
            logger.exception("Error when show qr code", exc_info=e)
            return f"Fail, {e}", 400

    def get(self):
        """
        Check and reserve device for display.
        return
        {"results": "OK", "reserve_id": "xxxxx"}
        or
        {"results": "BUSY"}
        """
        try:
            session_id = qr.get_display()
            if session_id:
                return session_id
            return {"results": "BUSY"}
        except Exception as e:
            logger.exception("Error when do update metrics post", exc_info=e)
            return f"Fail, {e}", 400

    def delete(self):
        """
        release display , clear session
        input:
        {"reserve_id": "xxxxx"}
        return {"results": "SUCCESS"} or {"results": "FAIL"}
        """
        try:
            data = request.json
            ret = qr.release_display(**data)
            return jsonify({"results": ret})
        except Exception as e:
            logger.exception("Error when do update metrics post", exc_info=e)
            return f"Fail, {e}", 400
