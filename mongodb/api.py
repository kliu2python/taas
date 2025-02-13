import json

from flask import (
    jsonify,
    request,
    abort
)
from flask_restful import Resource

from rest import RestApi
from mongodb.client import MongoDBClient

rest = RestApi(base_route="/api/v1/mongodb")


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
        collection_name = request.args.get("collection")
        if not db_name or not collection_name:
            abort(500, description="Missing 'db' or 'collection' parameter.")
        data = request.get_json()
        if not data:
            abort(500, description="Missing JSON body for document.")

        client = MongoDBClient(db_name=db_name)
        result = client.insert_one(collection_name, data)
        return jsonify({"inserted_id": str(result.inserted_id)})


@rest.route("/document/find")
class FindDocuments(Resource):
    def get(self):
        db_name = request.args.get("db")
        collection_name = request.args.get("collection")
        if not db_name or not collection_name:
            abort(500, description="Missing 'db' or 'collection' parameter.")

        filter_str = request.args.get("filter")
        if filter_str:
            try:
                filter_query = json.loads(filter_str)
            except Exception:
                abort(500, description="Invalid filter JSON.")
        else:
            filter_query = {}

        client = MongoDBClient(db_name=db_name)
        results = client.find(collection_name, filter_query)
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
