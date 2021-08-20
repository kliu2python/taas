import collections
import datetime
import json
import uuid

from cassandra.cqlengine import ValidationError

from utils.logger import get_logger

logger = get_logger()


class ItemExistsError(Exception):
    pass


class ApiBase:
    __db_model__ = None
    __unique_values__ = True
    __column_udt_map__ = None

    @classmethod
    def handle_customer_type(cls, data):
        udt_map = cls.__column_udt_map__
        if udt_map:
            for col, udt in udt_map.items():
                col_data = data.get(col)
                if col_data:
                    if isinstance(col_data, list):
                        new_data = []
                        for d in col_data:
                            new_data.append(udt(**d))
                    elif isinstance(col_data, dict):
                        new_data = udt(**col_data)
                    else:
                        raise TypeError(
                            f"{col} should be a dict or a list of dict"
                        )
                    data[col] = new_data
        return data

    @classmethod
    def create(cls, data, unique=None, pk=None):
        ret_code = 201
        ret_msg = None
        unique_value = cls.__unique_values__
        if unique is not None:
            unique_value = unique
        try:
            if unique_value:
                if pk is None:
                    pk = str(cls.__db_model__.pk)
                filter_dict = {}
                if isinstance(pk, str):
                    filter_dict[pk] = data.get(pk)
                elif isinstance(pk, list):
                    for k in pk:
                        filter_dict[k] = data.get(k)
                else:
                    raise TypeError("pk should be str or list")
                if cls.__db_model__.objects(**filter_dict).count() == 0:
                    data = cls.handle_customer_type(data)
                    cls.__db_model__.create(**data)
                else:
                    raise ItemExistsError
            else:
                cls.__db_model__.create(**data)
        except ValidationError as e:
            ret_msg = f"Validation Error, please check your input data, {e}"
            ret_code = 400
        except (KeyError, TypeError) as e:
            ret_msg = f"key or Type error in custom type: {e}"
            ret_code = 400
        except ItemExistsError:
            ret_msg = f"Item already exists"
            ret_code = 403
        except Exception as e:
            ret_msg = f"{e}"
            ret_code = 500
            logger.exception("", exc_info=e)
        return ret_msg, ret_code

    @classmethod
    def update_one(cls, data, **filters):
        ret_code = 200
        ret_msg = None
        try:
            db_item = cls.__db_model__.objects(**filters)
            if len(db_item) > 1:
                return "filter is required for update one db item", 400
            if db_item:
                data = cls.handle_customer_type(data)
                if hasattr(cls.__db_model__, "updated_at"):
                    data["updated_at"] = datetime.datetime.utcnow()
                db_item[0].update(**data)
            else:
                return (
                    f"DB db object in {cls.__db_model__} is not found "
                    f"with filter {filters}", 404
                )
        except ValidationError as e:
            ret_msg = f"Validation Error, please check your input data, {e}"
            ret_code = 400
        except Exception as e:
            ret_msg = f"{e}"
            ret_code = 500

        return ret_msg, ret_code

    @classmethod
    def delete(cls, **filters):
        ret_code = 200
        ret_msg = None
        try:
            db_items = cls.__db_model__.objects(**filters)
            if db_items:
                for item in db_items:
                    item.delete()
            else:
                return f"No db item fould with filter {filters}", 404
        except ValidationError as e:
            ret_msg = f"Validation Error, please check your input data, {e}"
            ret_code = 400
        except Exception as e:
            ret_msg = f"{e}"
            ret_code = 500

        return ret_msg, ret_code

    @classmethod
    def read_to_json(cls, **filters):
        def default(x):
            if isinstance(x, datetime.datetime):
                return f"{x}"
            if isinstance(x, uuid.UUID):
                return str(x)
            for udt in cls.__column_udt_map__.values():
                if isinstance(x, udt):
                    return dict((k, v) for (k, v) in x.items())
            return type(x).__qualname__

        rows = cls.__db_model__.objects(**filters).all()
        ret_msg = []
        if len(rows) > 0:
            for row in rows:
                msg_dict = dict((k, v) for (k, v) in row.items())
                ret_msg.append(msg_dict)
        ret_msg = {"data": ret_msg}
        ret_msg = json.dumps(
            ret_msg,
            default=default
        )
        return json.loads(ret_msg)

    @classmethod
    def read(
            cls, columns, limit=None, order_by=None, **filters
    ):
        if order_by is None:
            order_by = []
        items = cls.__db_model__.objects(
            **filters
        ).all().allow_filtering().order_by(*order_by).limit(limit)
        if isinstance(columns, str):
            columns = [columns]
        if len(items) == 1:
            ret = {}
            for column in columns:
                ret[column] = items[0][column]
        else:
            ret = collections.defaultdict(list)
            for item in items:
                for column in columns:
                    ret[column].append(item[column])
        return ret
