import copy

import allure
import pytest

from api.common_api import CommonApi
from testcases.support import assert_api_response, cases, make_unique_email, set_case_severity


def runtime_case(data, key="email", tag="weather-api-test"):
    case = copy.deepcopy(data)
    if case.get(key) == "__RUNTIME_UNREGISTERED_EMAIL__":
        case[key] = make_unique_email(tag)
    return case


@allure.feature("气象分析系统接口自动化")
class TestWeatherApiPublicFlows:
    def setup_class(self):
        self.api = CommonApi()

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_check_email_cases"))
    def test_check_email(self, data):
        data = runtime_case(data, tag="check-email")
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        response = self.api.check_email(data["email"])
        body = assert_api_response(response, data)
        assert isinstance(body.get("message"), str)

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_send_register_code_cases"))
    def test_send_register_code(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        response = self.api.send_register_code(data["email"])
        assert_api_response(response, data)

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_send_reset_code_cases"))
    def test_send_reset_code(self, data):
        data = runtime_case(data, tag="send-reset")
        allure.dynamic.title(data["case_name"])
        set_case_severity("minor")
        response = self.api.send_reset_code(data["email"])
        assert_api_response(response, data)

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_verify_code_negative_cases"))
    def test_verify_code_negative(self, data):
        data = runtime_case(data, tag="verify-code")
        allure.dynamic.title(data["case_name"])
        set_case_severity("normal")
        response = self.api.verify_code(data["email"], data["code"], data["type"])
        assert_api_response(response, data)

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_register_negative_cases"))
    def test_register_negative(self, data):
        data = runtime_case(data, tag="register")
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        response = self.api.register(data["email"], data["password"], data["verify_token"])
        assert_api_response(response, data)

    @allure.story("公共接口")
    @pytest.mark.parametrize("data", cases("public_reset_password_negative_cases"))
    def test_reset_password_negative(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        response = self.api.reset_password(data["email"], data["new_password"], data["verify_token"])
        assert_api_response(response, data)
