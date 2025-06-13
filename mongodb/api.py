import json
import re
from datetime import datetime

from bson import ObjectId
from flask import (
    jsonify,
    request,
    abort
)
from flask_restful import Resource

from rest import RestApi
from mongodb.client import MongoDBClient
from dateutil.parser import isoparse   # pip install python-dateutil
from urllib.parse import unquote_plus

rest = RestApi(base_route="/api/v1/mongodb")
_ts_key_pattern = re.compile(r'.*(time|date|at)$', re.IGNORECASE)
_ts_key_pattern_rr = re.compile(r'.*[_-]at$')


def _parse_date_filters(obj):
    """
    Recursively convert any { '$gte': '2025-04-20T00:00:00', ... }
    into { '$gte': datetime(...), ... }
    """
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            # for comparison operators with ISO‑string values
            if k in ("$gte", "$lte", "$gt", "$lt") and isinstance(v, str):
                try:
                    new[k] = isoparse(v)
                except ValueError:
                    new[k] = v
            elif isinstance(v, str):
                new[k] = v
            elif isinstance(v, int):
                new[k] = v
            else:
                new[k] = _parse_date_filters(v)
        return new

    elif isinstance(obj, list):
        return [_parse_date_filters(i) for i in obj]
    elif isinstance(obj, str):
        key, val = obj.split("=")
        return {key: val}
    elif isinstance(obj, dict):
        return obj
    else:
        raise Exception("filter is illegal")


def normalize_timestamps(data: dict) -> None:
    """
    In-place: Converts any string value whose key looks like a timestamp
    into a datetime, if it can be parsed as ISO8601.
    """
    for key, val in list(data.items()):
        if isinstance(val, str) and _ts_key_pattern.match(key):
            try:
                data[key] = isoparse(val)
            except ValueError:
                # not a parseable timestamp → leave as string
                pass


def denormalize_and_serialize(obj):
    """
    In-place:
      - datetime → ISO string (for keys matching _ts_key_pattern),
      - ObjectId → str(ObjectId),
    Recurses into lists and dicts.
    """
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, datetime) and _ts_key_pattern.match(k):
                obj[k] = v.isoformat().replace('+00:00', 'Z')
            elif isinstance(v, ObjectId):
                obj[k] = str(v)
            else:
                denormalize_and_serialize(v)
    elif isinstance(obj, list):
        for item in obj:
            denormalize_and_serialize(item)

@rest.route("/collection")
class ListCollectionsOnDatabase(Resource):
    def get(self):
        database_name = request.args.get("db")
        if not database_name:
            abort(500, description="failed, required a db name")
        results = MongoDBClient(db_name=database_name).list_collections()
        return jsonify({"collections": results})


@rest.route("/document/insert")
class InsertDocument(Resource):
    def post(self):
        db_name = request.args.get("db")
        coll_name = request.args.get("collection")
        if not db_name or not coll_name:
            abort(400, description="Missing 'db' or 'collection' parameter.")
        data = request.get_json()
        if not data:
            abort(400, description="Missing JSON body for document.")

        normalize_timestamps(data)

        client = MongoDBClient(db_name=db_name)
        result = client.insert_one(coll_name, data)
        return jsonify({"inserted_id": str(result.inserted_id)})


@rest.route("/document/find")
class FindDocuments(Resource):
    def get(self):
        db_name = request.args.get("db")
        collection_name = request.args.get("collection")
        if not db_name or not collection_name:
            abort(500, description="Missing 'db' or 'collection' parameter.")

        filter_str = request.args.get("filter")
        projection_query = request.args.get("projection", "")
        if filter_str:
            try:
                # 1) URL‑decode the JSON text:
                decoded = unquote_plus(filter_str)
                # 2) Parse it into a Python dict:
                filter_query = json.loads(decoded)
            except Exception as e:
                abort(400,
                      description=f"Invalid filter JSON: {e}")
            filter_query = _parse_date_filters(filter_query)
        else:
            filter_query = {}
        if projection_query:
            try:
                # 1) URL‑decode the JSON text:
                decoded = unquote_plus(projection_query)
                # 2) Parse it into a Python dict:
                projection_query = json.loads(decoded)
            except Exception as e:
                abort(400,
                      description=f"Invalid filter JSON: {e}")
            projection_query = _parse_date_filters(projection_query)
            projection_query["_id"] = 0

        client = MongoDBClient(db_name=db_name)
        results = client.find(collection_name, filter_query,
                              projection=projection_query)
        denormalize_and_serialize(results)
        return jsonify({"documents": results})


@rest.route("/document/update")
class UpdateDocument(Resource):
    def put(self):
        db_name = request.args.get("db")
        collection_name = request.args.get("collection")
        if not db_name or not collection_name:
            abort(500, description="Missing 'db' or 'collection' parameter.")

        data = request.get_json()
        if not data or "filter" not in data or "update" not in data:
            abort(
                500,
                description="JSON body must include 'filter' and 'update' keys."
            )

        filter_query = data["filter"]
        update_query = data["update"]
        upsert = data.get("upsert", False)

        client = MongoDBClient(db_name=db_name)
        result = client.update_one(
            collection_name, filter_query, update_query, upsert=upsert
        )
        return jsonify({
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        })


@rest.route("/document/delete")
class DeleteDocument(Resource):
    def delete(self):
        db_name = request.args.get("db")
        collection_name = request.args.get("collection")
        if not db_name or not collection_name:
            abort(500, description="Missing 'db' or 'collection' parameter.")

        data = request.get_json()
        if not data or "filter" not in data:
            abort(500, description="JSON body must include 'filter' key.")

        filter_query = data["filter"]
        client = MongoDBClient(db_name=db_name)
        result = client.delete_one(collection_name, filter_query)
        return jsonify({"deleted_count": result.deleted_count})
