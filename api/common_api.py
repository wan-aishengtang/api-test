from common.auth_util import AuthUtil
from common.rest_client import RestClient
from config import settings


class CommonApi(RestClient):
    def __init__(self, api_root_url=None):
        super().__init__()
        self.api_root_url = (api_root_url or settings.BASE_URL).rstrip("/")
        self.auth = AuthUtil(self)
        self.last_response = None

    def request(self, method, url, **kwargs):
        response = super().request(method, url, **kwargs)
        self.last_response = response
        return response

    def _url(self, path):
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.api_root_url}{path}"

    @staticmethod
    def _json_headers(extra=None):
        headers = {"Content-Type": "application/json"}
        if extra:
            headers.update(extra)
        return headers

    def login(self, email, password, force_login=False):
        url = self._url("/weather/user/login/")
        data = {"email": email, "password": password, "force_login": force_login}
        return self.request("POST", url, json=data, headers=self._json_headers())

    def refresh_token(self):
        url = self._url("/weather/user/refresh/")
        return self.request("POST", url, json={}, headers=self._json_headers())

    def logout(self):
        url = self._url("/weather/user/logout/")
        headers = self._json_headers(self.auth.bearer_header(self.auth.access_token))
        return self.request("POST", url, json={}, headers=headers)

    def issue_guest_token(self):
        url = self._url("/weather/user/guest-token/")
        headers = self._json_headers(self.auth.public_headers())
        return self.request("POST", url, json={}, headers=headers)

    def send_register_code(self, email):
        url = self._url("/weather/user/send-register-code/")
        data = {"email": email}
        headers = self._json_headers(self.auth.public_headers(data))
        return self.request("POST", url, json=data, headers=headers)

    def check_email(self, email):
        url = self._url("/weather/user/check-email/")
        return self.request("GET", url, params={"email": email})

    def verify_code(self, email, code, code_type):
        url = self._url("/weather/user/verify-code/")
        data = {"email": email, "code": code, "type": code_type}
        return self.request("POST", url, json=data, headers=self._json_headers())

    def register(self, email, password, verify_token):
        url = self._url("/weather/user/register/")
        data = {"email": email, "password": password, "verify_token": verify_token}
        return self.request("POST", url, json=data, headers=self._json_headers())

    def send_reset_code(self, email):
        url = self._url("/weather/user/send-reset-code/")
        data = {"email": email}
        headers = self._json_headers(self.auth.public_headers(data))
        return self.request("POST", url, json=data, headers=headers)

    def reset_password(self, email, new_password, verify_token):
        url = self._url("/weather/user/reset-password/")
        data = {
            "email": email,
            "new_password": new_password,
            "verify_token": verify_token,
        }
        return self.request("POST", url, json=data, headers=self._json_headers())

    def resolve_location_id(self, keyword, auth_mode=None):
        response = self.search_location(keyword, auth_mode=auth_mode)
        body = response.json() if response.headers.get("Content-Type", "").startswith("application/json") else {}
        if response.status_code != 200 or body.get("code") != 200:
            return None

        for item in body.get("data") or []:
            location_id = item.get("id")
            if location_id:
                return location_id
        return None

    def get_history_weather(self, city="杭州", location=None, year=None, month=None, lang="zh", unit="m", auth_mode=None):
        resolved_location = location or (self.resolve_location_id(city, auth_mode=auth_mode) if city else None)
        url = self._url("/weather/user/weather/history")
        params = {"location": resolved_location, "lang": lang, "unit": unit}
        params = {key: value for key, value in params.items() if value not in (None, "")}
        headers = self.auth.build_mode_headers(mode=auth_mode, params=params)
        return self.request("GET", url, params=params, headers=headers)

    def get_weather_now(self, location, auth_mode=None):
        return self.get_realtime_weather(location=location, auth_mode=auth_mode)

    def get_realtime_weather(self, location, auth_mode=None):
        url = self._url("/weather/user/weather/now")
        params = {"location": location}
        headers = self.auth.build_mode_headers(mode=auth_mode, params=params)
        return self.request("GET", url, params=params, headers=headers)

    def get_predict_weather(self, city=None, location=None, now_location=None, lang="zh", unit="m", auth_mode=None):
        resolved_location = location or (self.resolve_location_id(city, auth_mode=auth_mode) if city else None)
        url = self._url("/weather/user/weather/predict")
        params = {
            "location": resolved_location,
            "now_location": now_location or resolved_location,
            "lang": lang,
            "unit": unit,
        }
        params = {key: value for key, value in params.items() if value not in (None, "")}
        headers = self.auth.build_mode_headers(mode=auth_mode, params=params)
        return self.request("GET", url, params=params, headers=headers)

    def search_location(self, keyword, auth_mode=None):
        url = self._url("/weather/user/location/search")
        params = {"q": keyword}
        headers = self.auth.build_mode_headers(mode=auth_mode, params=params)
        return self.request("GET", url, params=params, headers=headers)

    def get_current_user(self):
        url = self._url("/weather/user/current/")
        return self.request("GET", url, headers=self.auth.bearer_header(self.auth.access_token))

    def save_profile(self, **profile):
        url = self._url("/weather/user/save/")
        headers = self._json_headers(self.auth.bearer_header(self.auth.access_token))
        return self.request("POST", url, json=profile, headers=headers)

    def check_username(self, username):
        url = self._url("/weather/user/check-username/")
        headers = self._json_headers(self.auth.bearer_header(self.auth.access_token))
        return self.request("POST", url, json={"username": username}, headers=headers)

    def upload_avatar(self, file_name, file_bytes, mime_type="image/png"):
        url = self._url("/weather/user/upload/avatar/")
        headers = self.auth.bearer_header(self.auth.access_token)
        files = {"avatar": (file_name, file_bytes, mime_type)}
        return self.request("POST", url, headers=headers, files=files)

    def list_admin_users(self, **query):
        url = self._url("/weather/admin/users/")
        params = {key: value for key, value in query.items() if value not in (None, "")}
        return self.request("GET", url, params=params, headers=self.auth.bearer_header(self.auth.access_token))

    def get_admin_user_detail(self, user_id):
        url = self._url(f"/weather/admin/users/{user_id}/info/")
        return self.request("GET", url, headers=self.auth.bearer_header(self.auth.access_token))

    def edit_admin_user(self, user_id, **payload):
        url = self._url(f"/weather/admin/users/{user_id}/edit/")
        headers = self._json_headers(self.auth.bearer_header(self.auth.access_token))
        return self.request("PUT", url, json=payload, headers=headers)

    def delete_admin_user(self, user_id):
        url = self._url(f"/weather/admin/users/{user_id}/delete/")
        return self.request("DELETE", url, headers=self.auth.bearer_header(self.auth.access_token))

    def batch_delete_admin_users(self, ids):
        url = self._url("/weather/admin/users/batch-delete/")
        headers = self._json_headers(self.auth.bearer_header(self.auth.access_token))
        return self.request("DELETE", url, json={"ids": ids}, headers=headers)

    def get_traffic_stats(self, days=None):
        url = self._url("/weather/admin/users/traffic-stats/")
        params = {"days": days} if days is not None else None
        return self.request("GET", url, params=params, headers=self.auth.bearer_header(self.auth.access_token))

    def get_server_status(self):
        url = self._url("/weather/admin/users/server-status/")
        return self.request("GET", url, headers=self.auth.bearer_header(self.auth.access_token))
