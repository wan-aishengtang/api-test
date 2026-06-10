import base64
import uuid
from pathlib import Path

import allure
import pytest

from common.yaml_util import read_yaml
from config import settings


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "weather_data.yaml"
TEST_DATA = read_yaml(DATA_PATH) or {}
SERVER_ERROR_CODES = {500, 502, 504}
NETWORK_ERROR_CODES = {599}

TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9l9QAAAABJRU5ErkJggg=="
)
SEVERITY_LEVELS = {
    "blocker": allure.severity_level.BLOCKER,
    "critical": allure.severity_level.CRITICAL,
    "normal": allure.severity_level.NORMAL,
    "minor": allure.severity_level.MINOR,
    "trivial": allure.severity_level.TRIVIAL,
}


def cases(name):
    return TEST_DATA.get(name, [])


def response_json(response):
    try:
        return response.json()
    except ValueError:
        allure.attach(response.text, "非 JSON 响应内容", allure.attachment_type.TEXT)
        return {}


def assert_api_response(response, case_data):
    allure.attach(response.text, "接口响应内容", allure.attachment_type.TEXT)
    if settings.ALLOW_NETWORK_ERRORS and response.status_code in NETWORK_ERROR_CODES:
        pytest.xfail(f"网络或代理异常: {response.text}")
    if settings.ALLOW_SERVER_ERRORS and response.status_code in SERVER_ERROR_CODES:
        pytest.xfail(f"服务端或第三方依赖异常: HTTP {response.status_code}")

    if "expect_http_status_any" in case_data:
        assert response.status_code in case_data["expect_http_status_any"]
    else:
        assert response.status_code == case_data["expect_http_status"]

    body = response_json(response)
    if "expect_code_any" in case_data and body:
        assert body.get("code") in case_data["expect_code_any"]
    elif "expect_code" in case_data and body:
        assert body.get("code") == case_data["expect_code"]
    if "expect_status" in case_data and body:
        assert body.get("status") == case_data["expect_status"]
    return body


def require_flag(enabled, reason):
    if not enabled:
        pytest.skip(reason)


def set_case_severity(level):
    allure.dynamic.severity(SEVERITY_LEVELS[level])


def prepare_login_session(api_client):
    if api_client.auth.access_token and api_client.auth.session_sign_key:
        return

    if not settings.USER_EMAIL or not settings.USER_PASSWORD:
        pytest.skip("未配置 WEATHER_USER_EMAIL / WEATHER_USER_PASSWORD")

    with allure.step("登录并获取正式模式会话"):
        response = api_client.auth.login(settings.USER_EMAIL, settings.USER_PASSWORD, force_login=True)

    body = assert_api_response(
        response,
        {"expect_http_status": 200, "expect_code": 200},
    )
    data = body.get("data", {})
    assert data.get("access_token") or data.get("token")
    assert data.get("sign_key") or data.get("session_sign_key")


def prepare_admin_session(api_client):
    if api_client.auth.access_token and api_client.auth.session_sign_key:
        return

    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        if settings.ALLOW_MISSING_ADMIN_CREDENTIALS:
            pytest.skip("未配置 WEATHER_ADMIN_EMAIL / WEATHER_ADMIN_PASSWORD")
        pytest.fail("缺少管理员账号配置")

    with allure.step("登录并获取管理员会话"):
        response = api_client.auth.login(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, force_login=True)

    body = assert_api_response(
        response,
        {"expect_http_status": 200, "expect_code": 200},
    )
    data = body.get("data", {})
    token = data.get("access_token") or data.get("token")
    assert token
    assert data.get("sign_key") or data.get("session_sign_key")


def prepare_guest_session(api_client):
    if api_client.auth.guest_token and api_client.auth.guest_sign_key:
        return

    with allure.step("签发并获取游客模式会话"):
        response = api_client.auth.issue_guest_session()

    body = response_json(response)
    if response.status_code == 401 and body.get("code") == 4010:
        pytest.xfail("当前环境要求先登录，游客 Token 签发接口返回 4010")

    body = assert_api_response(
        response,
        {"expect_http_status": 200, "expect_code": 200},
    )
    data = body.get("data", {})
    assert data.get("guest_token") or response.headers.get("X-Guest-Token") or response.headers.get("x-guest-token")
    assert data.get("sign_key")


def make_unique_email(tag):
    return f"{tag}-{uuid.uuid4().hex[:12]}@example.com"


def tiny_avatar_payload():
    return ("tiny-avatar.png", TINY_PNG_BYTES, "image/png")
