import hashlib
import time
import uuid


class AuthUtil:
    """Unified auth helper for public, guest and logged-in sessions."""

    PUBLIC_SIGN_KEY = "WEATHER_APP_SECURE_2025"

    def __init__(self, api_client):
        self.api_client = api_client
        self.access_token = None
        self.session_sign_key = None
        self.guest_token = None
        self.guest_sign_key = None

    @staticmethod
    def generate_signature(params=None, sign_key=None):
        if not sign_key:
            raise RuntimeError("sign_key is empty; initialize the target auth mode first")

        params = params or {}
        timestamp = str(int(time.time() * 1000))
        nonce = f"{uuid.uuid4().hex[:16]}{int(time.time())}"

        filtered_params = {
            key: value
            for key, value in params.items()
            if value is not None and value != ""
        }
        param_str = "&".join(f"{key}={filtered_params[key]}" for key in sorted(filtered_params))
        raw_str = f"{param_str}&timestamp={timestamp}&nonce={nonce}&secret={sign_key}"
        sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest().upper()

        return {
            "X-Sign": sign,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
        }

    @staticmethod
    def bearer_header(access_token):
        if not access_token:
            return {}
        if access_token.startswith("Bearer "):
            return {"Authorization": access_token}
        return {"Authorization": f"Bearer {access_token}"}

    def login(self, email, password, force_login=False):
        response = self.api_client.login(email, password, force_login=force_login)
        data = self._response_data(response, raise_on_error=False)
        if data:
            self.access_token = data.get("access_token") or data.get("token")
            self.session_sign_key = data.get("sign_key") or data.get("session_sign_key")
        return response

    def refresh_access_token(self):
        response = self.api_client.refresh_token()
        data = self._response_data(response, raise_on_error=False)
        if data:
            self.access_token = data.get("access_token") or data.get("token")
            self.session_sign_key = data.get("sign_key") or data.get("session_sign_key")
        return response

    def issue_guest_session(self, force=False):
        if self.guest_token and self.guest_sign_key and not force:
            return self.api_client.last_response

        response = self.api_client.issue_guest_token()
        data = self._response_data(response, raise_on_error=False)
        if data:
            self.guest_token = (
                data.get("guest_token")
                or response.headers.get("X-Guest-Token")
                or response.headers.get("x-guest-token")
            )
            self.guest_sign_key = data.get("sign_key")
        return response

    def get_guest_token(self, force=False):
        if self.guest_token and not force:
            return self.guest_token
        self.issue_guest_session(force=force)
        return self.guest_token

    def public_headers(self, params=None, extra=None):
        headers = self.generate_signature(params=params, sign_key=self.PUBLIC_SIGN_KEY)
        if extra:
            headers.update(extra)
        return headers

    def login_headers(self, params=None, extra=None, access_token=None):
        token = access_token or self.access_token
        sign_key = self.session_sign_key
        headers = self.bearer_header(token)
        headers.update(self.generate_signature(params=params, sign_key=sign_key))
        if extra:
            headers.update(extra)
        return headers

    def guest_headers(self, params=None, extra=None, guest_token=None, force=False):
        token = guest_token or self.get_guest_token(force=force)
        if not self.guest_sign_key:
            raise RuntimeError("guest_sign_key is empty; call issue_guest_session first")
        headers = {"X-Guest-Token": token} if token else {}
        headers.update(self.generate_signature(params=params, sign_key=self.guest_sign_key))
        if extra:
            headers.update(extra)
        return headers

    def build_mode_headers(self, mode=None, params=None, extra=None):
        if mode == "login":
            return self.login_headers(params=params, extra=extra)
        if mode == "guest":
            return self.guest_headers(params=params, extra=extra)
        if mode == "public":
            return self.public_headers(params=params, extra=extra)
        return extra.copy() if extra else {}

    @staticmethod
    def _response_data(response, raise_on_error=True):
        try:
            body = response.json()
        except ValueError:
            if raise_on_error:
                raise RuntimeError(f"auth request returned non-JSON body: {response.status_code} {response.text}")
            return {}

        if body.get("code") != 200 and body.get("status") != "success":
            if raise_on_error:
                raise RuntimeError(f"auth request failed: {response.status_code} {body}")
            return {}
        return body.get("data") or {}
