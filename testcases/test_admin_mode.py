import allure
import pytest

from api.common_api import CommonApi
from config import settings
from testcases.support import assert_api_response, cases, prepare_admin_session, prepare_login_session, set_case_severity


@allure.feature("气象分析系统接口自动化")
class TestWeatherApiAdminMode:
    def setup_class(self):
        self.user_api = CommonApi()
        self.admin_api = CommonApi()

    @allure.story("管理员鉴权")
    @pytest.mark.parametrize("data", cases("admin_forbidden_cases"))
    def test_admin_endpoints_forbidden_for_normal_user(self, data):
        allure.dynamic.title(data["case_name"])
        if data["api"] in {"admin_edit_user", "admin_delete_user", "admin_batch_delete_users"}:
            set_case_severity("blocker")
        else:
            set_case_severity("critical")
        prepare_login_session(self.user_api)

        if data["api"] == "admin_user_list":
            response = self.user_api.list_admin_users(page=1, page_size=5)
        elif data["api"] == "admin_traffic_stats":
            response = self.user_api.get_traffic_stats(days=7)
        elif data["api"] == "admin_server_status":
            response = self.user_api.get_server_status()
        elif data["api"] == "admin_edit_user":
            response = self.user_api.edit_admin_user(
                data["target_user_id"],
                user_role="NORMAL",
                is_banned=False,
            )
        elif data["api"] == "admin_delete_user":
            response = self.user_api.delete_admin_user(data["target_user_id"])
        elif data["api"] == "admin_batch_delete_users":
            response = self.user_api.batch_delete_admin_users(data["ids"])
        else:
            pytest.fail(f"未支持的管理员鉴权校验接口: {data['api']}")

        assert_api_response(response, data)

    @allure.story("管理员能力")
    @pytest.mark.parametrize("data", cases("admin_success_list_cases"))
    def test_admin_user_list(self, data):
        allure.dynamic.title(data["case_name"])
        set_case_severity("critical")
        prepare_admin_session(self.admin_api)

        response = self.admin_api.list_admin_users(page=data["page"], page_size=data["page_size"])
        body = assert_api_response(response, data)
        assert isinstance(body.get("data"), list)
        assert isinstance(body.get("total"), int)

        if body["data"]:
            user_id = body["data"][0]["id"]
            detail_response = self.admin_api.get_admin_user_detail(user_id)
            detail_body = assert_api_response(
                detail_response,
                {"expect_http_status": 200, "expect_status": "success"},
            )
            assert (detail_body.get("data") or {}).get("id") == user_id

    @allure.story("管理员能力")
    @pytest.mark.parametrize("data", cases("admin_success_system_cases"))
    def test_admin_system_endpoints(self, data):
        allure.dynamic.title(data["case_name"])
        if data.get("days") is not None:
            set_case_severity("normal")
        else:
            set_case_severity("critical")
        prepare_admin_session(self.admin_api)

        if "流量" in data["case_name"]:
            response = self.admin_api.get_traffic_stats(days=data.get("days"))
            body = assert_api_response(response, data)
            stats = body.get("data") or {}
            assert "today" in stats
            assert "daily" in stats
        else:
            response = self.admin_api.get_server_status()
            body = assert_api_response(response, data)
            status = body.get("data") or {}
            assert "cpu" in status
            assert "system" in status

    @allure.story("管理员能力")
    def test_admin_delete_requires_protected_operator(self):
        set_case_severity("blocker")
        allure.dynamic.title("管理员删除用户")
        if not settings.ADMIN_EMAIL or settings.ADMIN_EMAIL == settings.PROTECTED_ADMIN_EMAIL:
            pytest.skip("未配置非受保护管理员账号，跳过删除权限差异校验")

        prepare_admin_session(self.admin_api)
        response = self.admin_api.delete_admin_user(1)
        body = assert_api_response(
            response,
            {"expect_http_status_any": [403, 404], "expect_status": "error"},
        )
        assert body.get("message")
