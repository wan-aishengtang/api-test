import allure
import pytest

from api.common_api import CommonApi
from config import settings
from testcases.support import (
    assert_api_response,
    cases,
    prepare_login_session,
    require_flag,
    set_case_severity,
    tiny_avatar_payload,
)


@allure.feature("气象分析系统接口自动化")
class TestWeatherApiFormalMode:
    def setup_class(self):
        self.api = CommonApi()

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_location_search_cases"))
    def test_location_search(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("normal")
        prepare_login_session(self.api)
        with allure.step("使用正式模式会话搜索地点"):
            response = self.api.search_location(keyword=data["keyword"], auth_mode="login")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), list)

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_realtime_weather_cases"))
    def test_realtime_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        prepare_login_session(self.api)
        with allure.step("使用正式模式会话签名查询实时天气"):
            response = self.api.get_realtime_weather(location=data["location"], auth_mode="login")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_history_weather_cases"))
    def test_history_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("normal")
        prepare_login_session(self.api)
        with allure.step("使用正式模式会话查询历史天气"):
            response = self.api.get_history_weather(
                city=data.get("city", "杭州"),
                year=data.get("year"),
                month=data.get("month"),
                auth_mode="login",
            )
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_predict_weather_cases"))
    def test_predict_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("normal")
        prepare_login_session(self.api)
        with allure.step("使用正式模式会话查询天气预测"):
            response = self.api.get_predict_weather(city=data["city"], auth_mode="login")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_user_profile_cases"))
    def test_current_user(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        prepare_login_session(self.api)
        with allure.step("使用正式模式 Authorization 获取当前登录用户信息"):
            response = self.api.get_current_user()
        body = assert_api_response(response, data)
        profile = body.get("data") or {}
        assert profile.get("email") == settings.USER_EMAIL

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_profile_save_cases"))
    def test_save_profile(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        prepare_login_session(self.api)

        current_body = assert_api_response(
            self.api.get_current_user(),
            {"expect_http_status": 200, "expect_code": 200},
        )
        current_profile = current_body.get("data") or {}
        payload = {
            "username": current_profile.get("username") or "Voisten",
            "phone": current_profile.get("phone") or "",
            "gender": current_profile.get("gender") or "SECRET",
            "birthday": current_profile.get("birthday") or "",
        }

        with allure.step("提交当前资料以验证保存接口"):
            response = self.api.save_profile(**payload)
        body = assert_api_response(response, data)
        saved = body.get("data") or {}
        assert saved.get("email") == settings.USER_EMAIL
        assert saved.get("username") == payload["username"]

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_check_username_cases"))
    def test_check_username(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        prepare_login_session(self.api)

        current_body = assert_api_response(
            self.api.get_current_user(),
            {"expect_http_status": 200, "expect_code": 200},
        )
        username = (current_body.get("data") or {}).get("username") or "Voisten"

        with allure.step("检查当前用户名可用性"):
            response = self.api.check_username(username)
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), bool)

    @allure.story("正式模式")
    @pytest.mark.parametrize("data", cases("formal_upload_avatar_cases"))
    def test_upload_avatar(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        require_flag(settings.ENABLE_UPLOAD_TESTS, "未开启 WEATHER_ENABLE_UPLOAD_TESTS")
        prepare_login_session(self.api)

        file_name, file_bytes, mime_type = tiny_avatar_payload()
        with allure.step("上传 1x1 PNG 验证头像接口"):
            response = self.api.upload_avatar(file_name, file_bytes, mime_type)
        body = assert_api_response(response, data)
        upload_data = body.get("data") or {}
        assert upload_data.get("avatar_path")
        assert upload_data.get("avatar_name")
