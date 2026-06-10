import allure
import pytest

from api.common_api import CommonApi
from config import settings
from testcases.support import assert_api_response, cases, set_case_severity


@allure.feature("气象分析系统接口自动化")
class TestWeatherApiAuth:
    def setup_class(self):
        self.api = CommonApi()

    @allure.story("鉴权能力")
    @pytest.mark.parametrize("data", cases("auth_guest_token_cases"))
    def test_issue_guest_token(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        with allure.step("发送游客模式 Token 签发请求"):
            response = self.api.auth.issue_guest_session(force=True)

        body = assert_api_response(response, data)
        auth_data = body.get("data", {})
        assert auth_data.get("guest_token") or response.headers.get("X-Guest-Token") or response.headers.get("x-guest-token")
        assert auth_data.get("sign_key")

    @allure.story("鉴权能力")
    @pytest.mark.parametrize("data", cases("auth_login_cases"))
    def test_user_login_and_refresh(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("blocker")
        email = data.get("email") or settings.USER_EMAIL
        password = data.get("password") or settings.USER_PASSWORD

        with allure.step("登录并获取正式模式 access token / sign_key"):
            login_response = self.api.auth.login(email, password, force_login=True)
        login_body = assert_api_response(login_response, data)
        login_data = login_body.get("data", {})
        assert login_data.get("access_token") or login_data.get("token")
        assert login_data.get("sign_key") or login_data.get("session_sign_key")

        with allure.step("使用 HttpOnly Cookie 中的 refresh token 刷新正式模式 access token / sign_key"):
            refresh_response = self.api.auth.refresh_access_token()
        refresh_body = assert_api_response(
            refresh_response,
            {"expect_http_status": 200, "expect_code": 200},
        )
        refresh_data = refresh_body.get("data", {})
        assert refresh_data.get("access_token") or refresh_data.get("token")
        assert refresh_data.get("sign_key") or refresh_data.get("session_sign_key")

    @allure.story("鉴权能力")
    @pytest.mark.parametrize("data", cases("auth_logout_cases"))
    def test_logout_invalidates_refresh(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("blocker")
        login_response = self.api.auth.login(settings.USER_EMAIL, settings.USER_PASSWORD, force_login=True)
        assert_api_response(login_response, {"expect_http_status": 200, "expect_code": 200})

        with allure.step("调用退出登录接口"):
            logout_response = self.api.logout()
        assert_api_response(logout_response, data)

        with allure.step("退出后 refresh 应失效"):
            refresh_response = self.api.auth.refresh_access_token()
        assert_api_response(
            refresh_response,
            {
                "expect_http_status": data["refresh_expect_http_status"],
                "expect_code": data["refresh_expect_code"],
            },
        )
