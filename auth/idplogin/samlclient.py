import os
import requests
import urllib3
import urllib.parse
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
REQUESTS_TIMEOUT = int(os.environ.get("REQUESTS_TIMEOUT", "5"))


class LoginError(Exception):
    pass


class SPError(Exception):
    pass


class SamlClient:
    @classmethod
    def init_login(cls, url):
        resp = requests.get(
            url,
            verify=False,
            allow_redirects=True,
            timeout=REQUESTS_TIMEOUT
        )
        if resp.status_code in [200]:
            soup = BeautifulSoup(resp.content, "lxml")
            new_resp = cls.handle_no_script(soup)
            if new_resp:
                resp = new_resp
            csrf_middleware_token = soup.input["value"]
            cookie = resp.headers.get("Set-Cookie")
            init_cookie = resp.history[-1].headers.get("Set-Cookie")
            url = resp.url
            return resp.status_code, {
                "csrf_token": csrf_middleware_token,
                "cookie": cookie,
                "init_cookie": init_cookie,
                "url": url
            }

        return resp.status_code, {}

    @classmethod
    def _send_assertion_request(cls, soup, init_cookie, **tag):
        form = soup.find(**tag)
        url = form["action"]
        method = form["method"]
        input_data = soup.find_all(name="input", type="hidden")
        payload = {}
        for data in input_data:
            name = data['name']
            value = data['value']
            payload[name] = value

        payload = urllib.parse.urlencode(payload)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": init_cookie
        }
        request_method = getattr(requests, method)
        resp = request_method(
            url,
            data=payload,
            headers=headers,
            verify=False,
            allow_redirects=True,
            timeout=REQUESTS_TIMEOUT
        )
        return resp

    @classmethod
    def handle_no_script(cls, soup):
        no_script = soup.find("noscript")
        if no_script:
            resp = cls._send_assertion_request(soup, name="form")
            return resp

    @classmethod
    def idp_login(cls, username, password, context):
        payload = (
            f"csrfmiddlewaretoken={context['csrf_token']}"
            f"&username={username}"
            f"&password={password}"
            f"&next=%2F"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": context["cookie"]
        }
        resp = requests.post(
            context["url"],
            verify=False,
            allow_redirects=True,
            headers=headers,
            data=payload,
            timeout=REQUESTS_TIMEOUT
        )
        return resp

    @classmethod
    def logout(cls, context, logout_data):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": logout_data.get("token")
        }
        resp = requests.get(
            f"{context.url}logout", 
            verify=False, 
            allow_redirects=False,
            headers=headers,
            timeout=REQUESTS_TIMEOUT
        )
        if resp.status_code == 302:
            url = resp.headers.get("location")
            headers = {
                "Cookie": f"csrftoken={logout_data.get('csrf_token')};"
                          f"{logout_data.get('cookie')}"
            }
            resp = requests.get(
                url, verify=False, headers=headers, timeout=REQUESTS_TIMEOUT
            )
            return resp

    @classmethod
    def get_logout_token(cls, cookie):
        tokens = cookie.split(",")
        for token in tokens:
            token = token.strip()
            if token.startswith("token="):
                return token.split(";")[0].strip()

    @classmethod
    def go_sp_page(cls, context, init_cookie):
        soup = BeautifulSoup(context, "lxml")
        resp = cls._send_assertion_request(
            soup, init_cookie=init_cookie, id="logged_in_post_form"
        )
        logout_token = cls.get_logout_token(
            resp.history[-1].headers.get("Set-Cookie")
        )
        return resp, logout_token

    @classmethod
    def login(cls, url, username, password):
        logout_data = {}
        status_code, context = cls.init_login(url)
        if status_code not in [200]:
            print("init login failed")
            return status_code, "init login failed"

        init_cookie = context.pop("init_cookie")
        logout_data.update(context)

        context = cls.idp_login(username, password, context)
        if context.status_code not in [200]:
            print("idp login failed")
            return context.status_code, "idp login failed"
        resp, token = cls.go_sp_page(context.content, init_cookie)
        logout_data["token"] = token
        return resp, logout_data
