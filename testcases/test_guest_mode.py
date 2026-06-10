import allure
import pytest

from api.common_api import CommonApi
from testcases.support import assert_api_response, cases, prepare_guest_session, set_case_severity


@allure.feature("气象分析系统接口自动化")
class TestWeatherApiGuestMode:
    def setup_class(self):
        self.api = CommonApi()

    @allure.story("游客模式")
    @pytest.mark.parametrize("data", cases("guest_location_search_cases"))
    def test_location_search(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        prepare_guest_session(self.api)
        with allure.step("使用游客模式会话搜索地点"):
            response = self.api.search_location(keyword=data["keyword"], auth_mode="guest")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), list)

    @allure.story("游客模式")
    @pytest.mark.parametrize("data", cases("guest_realtime_weather_cases"))
    def test_realtime_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("normal")
        prepare_guest_session(self.api)
        with allure.step("使用游客模式 Token 和签名查询实时天气"):
            response = self.api.get_realtime_weather(location=data["location"], auth_mode="guest")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)
        assert response.headers.get("X-Guest-Quota-Remaining") is not None

    @allure.story("游客模式")
    @pytest.mark.parametrize("data", cases("guest_history_weather_cases"))
    def test_history_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        prepare_guest_session(self.api)
        with allure.step("使用游客模式 Token 查询历史天气"):
            response = self.api.get_history_weather(
                city=data.get("city", "杭州"),
                year=data.get("year"),
                month=data.get("month"),
                auth_mode="guest",
            )
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)

    @allure.story("游客模式")
    @pytest.mark.parametrize("data", cases("guest_predict_weather_cases"))
    def test_predict_weather(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        prepare_guest_session(self.api)
        with allure.step("使用游客模式 Token 查询天气预测"):
            response = self.api.get_predict_weather(city=data["city"], auth_mode="guest")
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), dict)

    @allure.story("异常场景")
    @pytest.mark.parametrize("data", cases("negative_cases"))
    def test_negative_cases(self, data):
        allure.dynamic.title(data["case_name"])
        if data["api"] == "weather_now":
            set_case_severity("critical")
        elif data["api"] in {"guest_token_without_signature", "register_code_without_signature"}:
            set_case_severity("normal")
        else:
            set_case_severity("minor")
        if data["api"] == "weather_now":
            response = self.api.get_realtime_weather(data["location"])
        elif data["api"] == "location_search":
            response = self.api.search_location(data["keyword"])
        elif data["api"] == "guest_token_without_signature":
            url = self.api._url("/weather/user/guest-token/")
            response = self.api.request("POST", url, json={}, headers={"Content-Type": "application/json"})
        elif data["api"] == "register_code_without_signature":
            url = self.api._url("/weather/user/send-register-code/")
            response = self.api.request(
                "POST",
                url,
                json={"email": data["email"]},
                headers={"Content-Type": "application/json"},
            )
        else:
            pytest.fail(f"未支持的异常场景接口: {data['api']}")
        assert_api_response(response, data)
