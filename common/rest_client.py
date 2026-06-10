import json

import requests

from config import settings


class RestClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = settings.USE_SYSTEM_PROXY

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", settings.REQUEST_TIMEOUT)
        try:
            return self.session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            if not settings.ALLOW_NETWORK_ERRORS:
                raise

            response = requests.Response()
            response.status_code = 599
            response.url = url
            response._content = json.dumps(
                {"code": 599, "message": f"请求异常: {exc}"},
                ensure_ascii=False,
            ).encode("utf-8")
            response.headers["Content-Type"] = "application/json"
            return response
