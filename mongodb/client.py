from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dateutil.parser import isoparse

from mongodb.conf import MONGODB_INFO
from utils.logger import get_logger

logger = get_logger()


class MongoDBClient:
    # Class-level client to reuse the connection pool
    _client = None

    def __init__(self, db_name="testdb"):
        """
        Initialize the MongoDB client and set the database.
        This will reuse the connection pool if already initialized.
        """
        self.uri = MONGODB_INFO.get("server")
        try:
            if MongoDBClient._client is None:
                MongoDBClient._client = MongoClient(self.uri)
                logger.info("MongoClient initialized and "
                            "connection pool created.")
            self.client = MongoDBClient._client

            # Use provided db_name or fallback to a default from config
            db = db_name if db_name else MONGODB_INFO.get("collection")
            self.db = self.client[db]
            logger.info(f"Connected to MongoDB database: {db}")
        except PyMongoError as e:
            logger.info(f"Error connecting to MongoDB: {e}")
            raise

    def get_collection(self, collection_name):
        """
        Retrieve a collection from the database.
        """
        return self.db[collection_name]

    # Create operations
    def insert_one(self, collection_name, document):
        """
        Insert a single document into a collection.
        """
        collection = self.get_collection(collection_name)
        if 'timestamp' in document and isinstance(document['timestamp'], str):
            logger.info("timestamp is still str, convert it")
            try:
                document['timestamp'] = isoparse(document['timestamp'])
            except ValueError:
                pass
        return collection.insert_one(document)

    def insert_many(self, collection_name, documents):
        """
        Insert multiple documents into a collection.
        """
        collection = self.get_collection(collection_name)
        return collection.insert_many(documents)

    # Read operations
    def find_one(self, collection_name, query, projection=None):
        """
        Find a single document matching the query.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one(query, projection)

    def find(self, collection_name, query, projection=None):
        """
        Find all documents matching the query.
        """
        collection = self.get_collection(collection_name)
        return list(collection.find(query, projection))

    def count_documents(self, collection_name, query):
        """
        Count documents in a collection matching the query.
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents(query)

    # Update operations
    def update_one(self, collection_name, filter_query, update_query,
                   upsert=False, use_set=True):
        """
        Update a single document in a collection. If `use_set` is True and the
        update_query doesn't contain an update operator (like '$set'),
        it will automatically wrap the update_query in a '$set' operator.
        """
        collection = self.get_collection(collection_name)

        if use_set:
            if not any(key.startswith('$') for key in update_query.keys()):
                update_query = {"$set": update_query}

        return collection.update_one(filter_query, update_query, upsert=upsert)

    def update_many(self, collection_name, filter_query, update_query,
                    upsert=False):
        """
        Update multiple documents in a collection.
        """
        collection = self.get_collection(collection_name)
        return collection.update_many(filter_query, update_query, upsert=upsert)

    def find_one_and_update(self, collection_name, filter_query, update_query,
                            **kwargs):
        """
        Atomically find a document and update it.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one_and_update(filter_query, update_query,
                                              **kwargs)

    # Delete operations
    def delete_one(self, collection_name, query):
        """
        Delete a single document matching the query.
        """
        collection = self.get_collection(collection_name)
        return collection.delete_one(query)

    def delete_many(self, collection_name, query):
        """
        Delete multiple documents matching the query.
        """
        collection = self.get_collection(collection_name)
        return collection.delete_many(query)

    def find_one_and_delete(self, collection_name, filter_query, **kwargs):
        """
        Atomically find a document and delete it.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one_and_delete(filter_query, **kwargs)

    def find_one_and_replace(self, collection_name, filter_query, replacement,
                             **kwargs):
        """
        Atomically find a document and replace it with a new document.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one_and_replace(filter_query, replacement,
                                               **kwargs)

    # Aggregation
    def aggregate(self, collection_name, pipeline):
        """
        Run an aggregation pipeline on a collection.
        """
        collection = self.get_collection(collection_name)
        return list(collection.aggregate(pipeline))

    # Index management
    def create_index(self, collection_name, keys, **kwargs):
        """
        Create an index on a collection.
        """
        collection = self.get_collection(collection_name)
        return collection.create_index(keys, **kwargs)

    def list_indexes(self, collection_name):
        """
        List all indexes in a collection.
        """
        collection = self.get_collection(collection_name)
        return list(collection.list_indexes())

    def drop_index(self, collection_name, index_name):
        """
        Drop a specific index from a collection.
        """
        collection = self.get_collection(collection_name)
        return collection.drop_index(index_name)

    # Collection management
    def list_collections(self):
        """
        List all collection names in the database.
        """
        return self.db.list_collection_names()

    def drop_collection(self, collection_name):
        """
        Drop a collection from the database.
        """
        return self.db.drop_collection(collection_name)

    def rename_collection(self, old_name, new_name, dropTarget=False):
        """
        Rename a collection in the database.
        """
        collection = self.get_collection(old_name)
        return collection.rename(new_name, dropTarget=dropTarget)

    # Transactions (requires MongoDB replica set or sharded cluster)
    def run_transaction(self, transaction_func):
        """
        Execute a set of operations in a transaction. The transaction_func
        should accept a session parameter and execute transactional operations.
        """
        with self.client.start_session() as session:
            with session.start_transaction():
                return transaction_func(session)

    # Close connection
    def close(self):
        """
        Close the MongoDB client connection.
        """
        # Warning: Closing the shared client affects all instances.
        self.client.close()
        logger.info("MongoDB connection closed.")


# Example usage:
if __name__ == "__main__":
    # Initialize client (using shared connection pool)
    mongo_client = MongoDBClient()

    # Insert a document
    doc = {"_id": 1234567890, "name": "Alice", "age": 30}
    result = mongo_client.insert_one("users", doc)
    print("Inserted ID:", result.inserted_id)

    # Find a document
    user = mongo_client.find_one("users", {"name": "Alice"})
    print("Found document:", user)

    # Update a document
    mongo_client.update_one("users", {"name": "Alice"}, {"$set": {"age": 31}})

    # Count documents
    count = mongo_client.count_documents("users", {})
    print("Number of users:", count)

    # List collections
    collections = mongo_client.list_collections()
    print("Collections in database:", collections)

    # Clean up (note: closing the shared connection)
    mongo_client.close()
