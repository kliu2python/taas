import datetime
import json

import scale.db.user as user_db
from scale.services.base import ApiBase

import scale.session.controller as controller


class User(ApiBase):
    __db_model__ = user_db.User


class Device(ApiBase):
    __db_model__ = user_db.Device
    __column_udt_map__ = {
        "logging": user_db.user_defined_types.Command
    }


class Group(ApiBase):
    __db_model__ = user_db.Group


class Plan(ApiBase):
    __db_model__ = user_db.Plan


class Template(ApiBase):
    __db_model__ = user_db.Templates


class Session(ApiBase):
    __db_model__ = user_db.Session
    __column_udt_map__ = {
        "logging": user_db.user_defined_types.Command
    }

    @classmethod
    def start(cls, user, plan_name):
        ret_code = 202
        try:
            plan = user_db.Plan.objects(user=user, name=plan_name)[0]
            if plan.status == 1:
                devices = plan.devices
                versions = []
                loggings = []
                logging_obj = []
                for device_info in devices:
                    owner, name = device_info.split(",")
                    device = user_db.Device.objects(user=owner, name=name)[0]
                    credential = device.credential
                    command_cred = {
                        "ssh_user": credential.get("username"),
                        "ssh_password": credential.get("password"),
                        "ssh_ip": device.ip
                    }
                    if device.logging:
                        for log_def in device.logging:
                            logging_obj.append(log_def)
                            cmd_info = log_def.serialize()
                            cmd_info.update(command_cred)
                            loggings.append(cmd_info)
                version = ",".join(versions)

                session_data = {
                    "session_id": plan.name,
                    "version": version,
                    "servers": [],
                    "target_platform": plan.target_platform,
                    "runner_count": plan.runner_count,
                    "loop": plan.loop,
                    "wait_seconds_after_notify": plan.wait_seconds_after_notify,
                    "deployment_config": plan.deployment_config,
                    "pods_adjust_momentum": plan.pods_adjust_momentum,
                    "force_new_session": plan.force_new_session,
                    "command_log_targets": loggings
                }
                try:
                    session_name = controller.create_session(session_data)
                except Exception as e:
                    return (
                        f"Error when start session from plan {plan.name}, {e}",
                        500
                    )
                session_data.pop("session_id", None)
                session_data.pop("servers", None)
                session_data["name"] = session_name
                session_data["user"] = user
                session_data["command_log_targets"] = logging_obj
                msg, code = cls.create(session_data, pk=["name", "user"])
                if code != 201:
                    controller.stop_session(session_name)
                    return f"Can not save session info to DB {msg}", 500
                ret_msg = session_name
            else:
                return f"Plan {plan.name} is disabled", 403
            return ret_msg, ret_code
        except Exception as e:
            return f"Exception when start session {e}", 500

    @classmethod
    def update(cls, data):
        try:
            session_id = data.pop("session_id")
            results = controller.update_session(
                data.get("data_dict"),
                data.get("common_dict"),
                session_id=session_id
            )
            ret_msg = results
            if results != "SUCCESS":
                return ret_msg, 400
            return ret_msg, 200
        except Exception as e:
            return f"Error when update session {e}", 500

    @classmethod
    def patch(cls, data):
        try:
            session_id = data.pop("session_id")
            results = controller.update_runner(
                data, session_id=session_id
            )
            if not isinstance(results, dict):
                return results, 404
            results["pods_adjust_momentum"] = results.pop("momentum")
            cls.update_one(results, id=session_id)
            return results, 200
        except Exception as e:
            return f"Error when update session {e}", 500

    @classmethod
    def stop(cls, user, session_name):
        try:
            ret_code = 500
            ret_msg = controller.stop_session(session_name)
            if "Fail" in ret_msg:
                ret_code = 403
            elif ret_msg is not None and ret_msg.startswith("http"):
                cls.update_one(
                    {"status": 2, "stopped_at": datetime.datetime.utcnow()},
                    user=user,
                    name=session_name
                )
                ret_code = 200
            else:
                ret_msg = "Error when stop Run"
            return ret_msg, ret_code
        except Exception as e:
            return f"Error when stop {e}", 500

    @classmethod
    def get(cls, user, session_name):
        def default(x):
            if isinstance(x, datetime.datetime):
                return f"{x}"
            return type(x).__qualname__

        results = cls.read_to_json(user=user, name=session_name)
        if results == "Fail":
            return results, 404
        json_dumps = json.dumps(
            results,
            default=default
        )
        return json.loads(json_dumps), 200
