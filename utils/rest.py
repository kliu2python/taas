import requests


def rest_call(
        server_ip, end_point, method="GET", param_dict=None, port=8000, **kwargs
):
    try:
        res = requests.request(
            url=f"http://{server_ip}:{port}{end_point}",
            params=param_dict,
            method=method,
            **kwargs
        )
        return res.content
    except Exception as e:
        print(f"call api with server_ip = {server_ip}, port = {port}"
              f"end_point = {end_point}, param: {param_dict}, exception: {e}")
