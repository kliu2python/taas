from flask_restful import reqparse

parser = reqparse.RequestParser()

# Add args you want to pass in
parser.add_argument("avd_name", type=str, default=False, required=False)
parser.add_argument("process_name", type=str, default=False, required=False)
parser.add_argument("ip", type=str, default=False, required=False)
parser.add_argument("platform_id", type=str, default=False, required=False)
parser.add_argument("request_id", type=str, default=False, required=False)
parser.add_argument("ops", type=str, default=False, required=False)
parser.add_argument(
    "session_id", type=str, default=False, required=False, location="args"
)
