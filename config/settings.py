import os

def get_bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_str_env(name, default=""):
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


DEFAULT_DOMAIN_BASE_URL = get_str_env("WEATHER_DOMAIN_BASE_URL", "https://www.weaquery.com").rstrip("/")
DEFAULT_SOURCE_BASE_URL = get_str_env("WEATHER_SOURCE_BASE_URL", "https://115.120.243.153").rstrip("/")
API_TARGET_MODE = get_str_env("WEATHER_API_TARGET_MODE", "domain").lower()
EXPLICIT_BASE_URL = get_str_env("WEATHER_API_BASE_URL", "").rstrip("/")

if EXPLICIT_BASE_URL:
    BASE_URL = EXPLICIT_BASE_URL
    ACTIVE_TARGET_MODE = "explicit"
elif API_TARGET_MODE == "source":
    BASE_URL = DEFAULT_SOURCE_BASE_URL
    ACTIVE_TARGET_MODE = "source"
else:
    BASE_URL = DEFAULT_DOMAIN_BASE_URL
    ACTIVE_TARGET_MODE = "domain"

USER_EMAIL = os.getenv("WEATHER_USER_EMAIL", "admin02@test.com")
USER_PASSWORD = os.getenv("WEATHER_USER_PASSWORD", "123456789")
ADMIN_EMAIL = os.getenv("WEATHER_ADMIN_EMAIL", "2711771004@qq.com")
ADMIN_PASSWORD = os.getenv("WEATHER_ADMIN_PASSWORD", "zxc123..")
PROTECTED_ADMIN_EMAIL = os.getenv("WEATHER_PROTECTED_ADMIN_EMAIL", "2431678846@qq.com")

REGISTER_CHECK_EMAIL = os.getenv("WEATHER_REGISTER_CHECK_EMAIL", USER_EMAIL)
RESET_CHECK_EMAIL = os.getenv("WEATHER_RESET_CHECK_EMAIL", USER_EMAIL)

ENABLE_EMAIL_SENDING_TESTS = as_bool(os.getenv("WEATHER_ENABLE_EMAIL_SENDING_TESTS", False))
ENABLE_MUTATION_TESTS = as_bool(os.getenv("WEATHER_ENABLE_MUTATION_TESTS", False))
ENABLE_UPLOAD_TESTS = as_bool(os.getenv("WEATHER_ENABLE_UPLOAD_TESTS", True))
ENABLE_ADMIN_MUTATION_TESTS = as_bool(os.getenv("WEATHER_ENABLE_ADMIN_MUTATION_TESTS", False))
ALLOW_MISSING_ADMIN_CREDENTIALS = as_bool(os.getenv("WEATHER_ALLOW_MISSING_ADMIN_CREDENTIALS", True))

ADMIN_MUTATION_USER_ID = os.getenv("WEATHER_ADMIN_MUTATION_USER_ID", "").strip()

REQUEST_TIMEOUT = float(os.getenv("WEATHER_API_TIMEOUT", "30"))
ALLOW_SERVER_ERRORS = as_bool(os.getenv("WEATHER_ALLOW_SERVER_ERRORS", True))
ALLOW_NETWORK_ERRORS = as_bool(os.getenv("WEATHER_ALLOW_NETWORK_ERRORS", True))
USE_SYSTEM_PROXY = as_bool(os.getenv("WEATHER_USE_SYSTEM_PROXY", False))
VERIFY_SSL = as_bool(os.getenv("WEATHER_VERIFY_SSL", False))
CA_BUNDLE = os.getenv("WEATHER_CA_BUNDLE", "").strip()
