from utils.samlclient import SamlClient


class InfoSiteSamlClient(SamlClient):
    def __init__(self, login_url, logout_url):
        self.cookies = None
        self.login_url = login_url
        self.logout_url = logout_url

    def login(self, **kwargs):
        context, self.cookies = super().login(self.login_url, **kwargs)
        return context

    def goto_page(self, url, **kwargs):
        return super().goto_page(url, self.cookies)

    def logout(self, **kwargs):
        return super().logout(self.logout_url, self.cookies)
