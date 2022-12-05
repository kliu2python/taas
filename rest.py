import os

import yaml

import features

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
        for k, v in self.callbacks.items():
            getattr(_api.app, k)(v)

    def route(self, route_path):
        def wrap(func):
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
            _api.add_resource(func, *routes)
            return func
        return wrap


def load_api_resource(api):
    global _api
    _api = api
    config_path = os.path.join(
        os.path.join(
            os.path.dirname(__file__),
            "service_config.yml"
        )
    )
    with open(config_path) as FILE:
        service_config = yaml.safe_load(FILE)
    if service_config:
        enabled_features = (
            service_config.get("service_config", {}).get("services", [])
        )
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
            print(f"!!!Feature is not exists for {feature}!!!")
    return _api


def get_loaded_api():
    return _loaded_api
