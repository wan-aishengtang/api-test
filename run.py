import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_SITE_PACKAGES = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
REPORT_ROOT = PROJECT_ROOT / "report"
RESULTS_DIR = REPORT_ROOT / "xml"
HTML_DIR = REPORT_ROOT / "html"
ARCHIVE_ROOT = REPORT_ROOT / "archive"
HISTORY_SOURCE_DIR = HTML_DIR / "history"
HISTORY_TARGET_DIR = RESULTS_DIR / "history"

if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

import pytest

from config import settings


def ensure_results_dir():
    """确保 Allure 原始结果目录和历史归档目录存在。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)


def mask_email(email):
    """对邮箱做简单脱敏，避免公开报告直接暴露完整账号。"""
    if not email or "@" not in str(email):
        return "***"

    local_part, domain = str(email).split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "*" if local_part else "***"
    else:
        masked_local = f"{local_part[0]}***{local_part[-1]}"
    return f"{masked_local}@{domain}"


def restore_history():
    """把上一份 HTML 报告中的 history 拷回 allure-results，保留趋势图。"""
    if not HISTORY_SOURCE_DIR.exists():
        return

    if HISTORY_TARGET_DIR.exists():
        shutil.rmtree(HISTORY_TARGET_DIR)
    shutil.copytree(HISTORY_SOURCE_DIR, HISTORY_TARGET_DIR)


def write_environment_file():
    """写入 Allure 环境信息面板。"""
    env_lines = [
        f"base_url={settings.BASE_URL}",
        f"user_email={mask_email(settings.USER_EMAIL)}",
        f"admin_email={mask_email(settings.ADMIN_EMAIL)}",
        f"request_timeout={settings.REQUEST_TIMEOUT}",
        f"allow_server_errors={settings.ALLOW_SERVER_ERRORS}",
        f"allow_network_errors={settings.ALLOW_NETWORK_ERRORS}",
        f"use_system_proxy={settings.USE_SYSTEM_PROXY}",
        f"verify_ssl={settings.VERIFY_SSL}",
        f"ca_bundle={settings.CA_BUNDLE or '(system default)'}",
        f"enable_email_sending_tests={settings.ENABLE_EMAIL_SENDING_TESTS}",
        f"enable_mutation_tests={settings.ENABLE_MUTATION_TESTS}",
        f"enable_upload_tests={settings.ENABLE_UPLOAD_TESTS}",
        f"enable_admin_mutation_tests={settings.ENABLE_ADMIN_MUTATION_TESTS}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"generated_at={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    (RESULTS_DIR / "environment.properties").write_text(
        "\n".join(env_lines) + "\n",
        encoding="utf-8",
    )


def write_executor_file():
    """写入运行器信息，区分本地执行和 GitHub Actions。"""
    now = datetime.now()
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        run_number = os.getenv("GITHUB_RUN_NUMBER") or now.strftime("%Y%m%d%H%M%S")
        repository = os.getenv("GITHUB_REPOSITORY", "unknown")
        server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
        run_id = os.getenv("GITHUB_RUN_ID", "")
        executor_payload = {
            "name": "GitHub Actions",
            "type": "github",
            "buildName": f"{repository} #{run_number}",
            "buildOrder": int(run_number),
            "buildUrl": f"{server_url}/{repository}/actions/runs/{run_id}" if run_id else "",
            "reportName": f"API-Test Allure Report {now.strftime('%Y/%m/%d %H:%M:%S')}",
        }
    else:
        executor_payload = {
            "name": "Local PowerShell",
            "type": "local",
            "buildName": f"API-Test {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "buildOrder": int(now.strftime("%Y%m%d%H%M%S")),
            "reportName": f"API-Test Allure Report {now.strftime('%Y/%m/%d %H:%M:%S')}",
        }

    (RESULTS_DIR / "executor.json").write_text(
        json.dumps(executor_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_categories_file():
    """定义失败分类规则，方便 Allure 聚合查看问题类型。"""
    categories_payload = [
        {
            "name": "Cloudflare 拦截",
            "matchedStatuses": ["skipped"],
            "messageRegex": ".*(Cloudflare|challenge.cloudflare.com|Just a moment|人机校验).*",
        },
        {
            "name": "鉴权/权限问题",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*(401|403|4010|4011|4012|4015|4016|4017|无权限|封禁|Token).*",
        },
        {
            "name": "断言失败",
            "matchedStatuses": ["failed"],
            "traceRegex": ".*AssertionError.*",
        },
        {
            "name": "网络或代理异常",
            "matchedStatuses": ["broken", "failed"],
            "messageRegex": ".*(599|HTTPSConnectionPool|SSLError|ProxyError|Read timed out|ConnectTimeout).*",
        },
        {
            "name": "服务端或第三方异常",
            "matchedStatuses": ["failed", "broken"],
            "messageRegex": ".*(500|502|504|服务端|第三方).*",
        },
        {
            "name": "跳过的安全开关",
            "matchedStatuses": ["skipped"],
            "messageRegex": ".*(WEATHER_ENABLE_|未开启|未配置).*",
        },
    ]
    (RESULTS_DIR / "categories.json").write_text(
        json.dumps(categories_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def archive_current_report(run_at):
    """把本次 xml/html 结果按时间归档，避免后续执行覆盖历史报告。"""
    run_id = run_at.strftime("%Y%m%d-%H%M%S")
    archive_dir = ARCHIVE_ROOT / run_id
    archive_xml_dir = archive_dir / "xml"
    archive_html_dir = archive_dir / "html"

    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    if RESULTS_DIR.exists():
        shutil.copytree(RESULTS_DIR, archive_xml_dir)
    if HTML_DIR.exists():
        shutil.copytree(HTML_DIR, archive_html_dir)

    metadata = {
        "run_id": run_id,
        "generated_at": run_at.strftime("%Y-%m-%d %H:%M:%S"),
        "html_index": str((archive_html_dir / "index.html").relative_to(ARCHIVE_ROOT)).replace("\\", "/"),
        "xml_dir": str(archive_xml_dir.relative_to(ARCHIVE_ROOT)).replace("\\", "/"),
    }
    (archive_dir / "meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (REPORT_ROOT / "latest-report.txt").write_text(
        f"latest_run_id={run_id}\n"
        f"generated_at={metadata['generated_at']}\n"
        f"html={archive_html_dir / 'index.html'}\n"
        f"xml={archive_xml_dir}\n",
        encoding="utf-8",
    )

    return run_id


def write_archive_index():
    """生成历史报告索引页，便于长期查看每次执行快照。"""
    rows = []
    for meta_file in sorted(ARCHIVE_ROOT.glob("*/meta.json"), reverse=True):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(
            {
                "run_id": meta.get("run_id", meta_file.parent.name),
                "generated_at": meta.get("generated_at", ""),
                "html_index": meta.get("html_index", ""),
                "xml_dir": meta.get("xml_dir", ""),
            }
        )

    row_html = "\n".join(
        (
            "<tr>"
            f"<td>{row['run_id']}</td>"
            f"<td>{row['generated_at']}</td>"
            f"<td><a href=\"./{row['html_index']}\">打开 HTML 报告</a></td>"
            f"<td><a href=\"./{row['xml_dir']}\">查看 XML 结果</a></td>"
            "</tr>"
        )
        for row in rows
    )
    if not row_html:
        row_html = "<tr><td colspan=\"4\">暂无历史报告</td></tr>"

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>API-Test 历史报告索引</title>
  <style>
    body {{
      font-family: "Microsoft YaHei", sans-serif;
      margin: 32px;
      background: #f7f8fa;
      color: #222;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    p {{
      color: #555;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid #e9ebef;
      text-align: left;
    }}
    th {{
      background: #f0f4f8;
    }}
    a {{
      color: #0b66d6;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .hint {{
      margin: 16px 0 24px;
    }}
  </style>
</head>
<body>
  <h1>API-Test 历史报告索引</h1>
  <p class="hint">每次执行 run.py 后，最新报告仍保存在 report/html，同时会在本目录自动生成一份带时间戳的归档。</p>
  <table>
    <thead>
      <tr>
        <th>运行编号</th>
        <th>生成时间</th>
        <th>HTML 报告</th>
        <th>XML 结果</th>
      </tr>
    </thead>
    <tbody>
      {row_html}
    </tbody>
  </table>
</body>
</html>
"""
    (ARCHIVE_ROOT / "index.html").write_text(index_html, encoding="utf-8")


if __name__ == "__main__":
    run_at = datetime.now()

    exit_code = pytest.main(
        [
            "-vs",
            "-p",
            "no:cacheprovider",
            "./testcases",
            "--alluredir",
            "./report/xml",
            "--clean-alluredir",
        ]
    )

    ensure_results_dir()
    restore_history()
    write_environment_file()
    write_executor_file()
    write_categories_file()

    subprocess.run(
        "allure generate ./report/xml -o ./report/html --clean",
        shell=True,
        check=False,
    )
    archive_current_report(run_at)
    write_archive_index()
    raise SystemExit(exit_code)
