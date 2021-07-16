from copy import deepcopy
from urllib.parse import urljoin

import requests

from .db import Tables


class HTTPClientMixin:
    def request(self, method, url, **kwargs):
        raise NotImplementedError('It is a mixin, please define it')

    def get(self, *args, **kwargs):
        return self.request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('delete', *args, **kwargs)


class V1APIClientSession(HTTPClientMixin):
    def __init__(self, base_url, cert_path=None, key_path=None, headers=None):
        self.base_url = base_url
        self.cert_path = cert_path
        self.key_path = key_path
        self.headers = headers

    def request(self, method, url, **kwargs):
        _headers = kwargs.pop('headers', None) or self.headers or {}
        if 'Content-Type' not in _headers:
            _headers['Content-Type'] = 'application/json'
        if not url.startswith('http'):
            url = urljoin(self.base_url, url)
        if self.cert_path is None and self.key_path is None:
            return requests.request(
                method,
                url,
                headers=_headers,
                verify=False,
                **kwargs
            )
        return requests.request(
            method,
            url,
            headers=_headers,
            cert=(self.cert_path, self.key_path),
            verify=False,
            **kwargs
        )


class FTMClient(V1APIClientSession):
    def __init__(
            self,
            ftc_server,
            cert_path=None,
            key_path=None,
            headers=None
    ):
        base_url = f'https://{ftc_server}/api/v1/'
        super().__init__(
            base_url, cert_path=cert_path, key_path=key_path, headers=headers
        )

    def token_activation(self, activation_code, ftm_info):
        act_data = deepcopy(ftm_info)
        act_data['d']['token_activation_code'] = activation_code
        resp = self.post('token/activation', json=act_data)
        assert resp.status_code == 200, resp.text
        assert resp.json() is not None
        return resp.json()

    def activate_user(self, user_name, db, ftm_info):
        user_id = db.query(Tables.USERS, "username", user_name)
        token = db.query(Tables.TOKENS, 'user_id', user_id[0].get("id"))
        assert len(token) == 1
        act_info = self.token_activation(
            token[0]['_activation_code'], ftm_info
        )
        return token[0], act_info
