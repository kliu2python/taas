import os
import yaml
import features
from flask_restx import Namespace, Resource  # Import Flask-RESTX Namespace and Resource
from functools import wraps

_api = None
_load_resource = __import__
_loaded_api = []


class RestApi:
    def __init__(self, base_route, **kwargs):
        if isinstance(base_route, str):
            self.base_routes = [base_route]
        elif isinstance(base_route, list):
            self.base_routes = base_route
        else:
            raise Exception("base route should be a string or list")
        self.callbacks = kwargs
        self.register_callbacks()

    def register_callbacks(self):
        # Register Flask app callbacks
        for k, v in self.callbacks.items():
            getattr(_api.app, k)(v)

    def route(self, route_path, methods=None):
        def wrap(func):
            # Create routes for the given path
            routes = []
            for base_route in self.base_routes:
                route = f"{base_route}{route_path}"
                routes.append(route)
                if "<" in route:
                    route_list = route.split("<")
                    routes = [route_list[0].rstrip("/")]
                    last_route = route_list[0]
                    for route_item in route_list[1:]:
                        last_route = f"{last_route}<{route_item}"
                        routes.append(last_route.rstrip("/"))

            # Create a Resource class dynamically from the function
            # Determine which HTTP methods to support (default to GET)
            supported_methods = methods if methods else ['GET']

            # Create a Resource class that wraps the function
            class DynamicResource(Resource):
                pass

            # Map the function to the appropriate HTTP method handlers
            for method in supported_methods:
                method_lower = method.lower()
                if method_lower == 'get':
                    DynamicResource.get = func
                elif method_lower == 'post':
                    DynamicResource.post = func
                elif method_lower == 'delete':
                    DynamicResource.delete = func
                elif method_lower == 'put':
                    DynamicResource.put = func
                elif method_lower == 'patch':
                    DynamicResource.patch = func

            # Set a meaningful name for the Resource class
            DynamicResource.__name__ = f"{func.__name__}_Resource"

            # Register the Resource class with Flask-RESTX
            _api.add_resource(DynamicResource, *routes)
            return func

        return wrap

    def add_namespace(self, namespace, path=None):
        """
        Registers a namespace to the API at a specified path.

        :param namespace: Flask-RESTPlus Namespace object
        :param path: The URL path to register the namespace at. If None, the namespace's default path is used.
        """
        if not isinstance(namespace, Namespace):
            raise Exception("Provided object is not a valid Namespace instance")

        # If no path is provided, use the namespace's default path
        namespace_path = path or namespace.path

        # Register the namespace with the Flask-RESTPlus API
        _api.add_namespace(namespace, path=namespace_path)


def load_api_resource(api):
    global _api
    _api = api
    config_path = os.path.join(
        os.path.join(os.path.dirname(__file__), "service_config.yml"))
    with open(config_path) as FILE:
        service_config = yaml.safe_load(FILE)
    if service_config:
        enabled_features = (
            service_config.get("service_config", {}).get("services", []))
    else:
        raise Exception("Failed to load service_config")

    _load_resource("welcome")

    for feature in enabled_features:
        print(f"Loading Feature: {feature}")
        _loaded_api.append(feature)
        feature_config = features.RESOURCE_MAPPING.get(feature)
        if feature_config is not None:
            _load_resource(feature_config)
        else:
            print(f"!!!Feature does not exist for {feature}!!!")

    return _api


def get_loaded_api():
    return _loaded_api
