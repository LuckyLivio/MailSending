#!/usr/bin/env python3
"""
send_smtp_cli.py
CLI 工具：重复发送测试邮件（用于合规的测试场景，例如发给自己）。
Features:
 - 支持 .env 和命令行参数
 - 支持 dry-run（仅打印）
 - 支持本地 MailHog 测试模式
 - 支持完全相同邮件或带序号的主题/正文
 - 简单重试与超时
"""
from __future__ import annotations
import argparse
import os
import sys
import time
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  # 读取 .env（如果存在）

# ---------- 默认配置（可通过 .env 或 CLI 覆盖） ----------
DEFAULTS = {
    "SMTP_HOST": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")),
    "SMTP_USER": os.getenv("SMTP_USER", ""),
    "SMTP_PASS": os.getenv("SMTP_PASS", ""),
    "TO_EMAIL": os.getenv("TO_EMAIL", os.getenv("SMTP_USER", "")),
    "SUBJECT_BASE": os.getenv("SUBJECT_BASE", "测试邮件 — 来自我的网站"),
    "BODY_PLAIN": os.getenv("BODY_PLAIN", "这是测试邮件（纯文本）。"),
    "BODY_HTML": os.getenv("BODY_HTML", "<p>这是测试邮件（HTML）。</p>"),
    "SEND_COUNT": int(os.getenv("SEND_COUNT", "5")),
    "DELAY_SEC": float(os.getenv("DELAY_SEC", "2.0")),
    "SUBJECT_ADD_INDEX": os.getenv("SUBJECT_ADD_INDEX", "true").lower() in ("1", "true", "yes", "y"),
    "IDENTICAL_BODY": os.getenv("IDENTICAL_BODY", "false").lower() in ("1", "true", "yes", "y"),
    "TIMEOUT": int(os.getenv("TIMEOUT", "60")),
    "RETRY": int(os.getenv("RETRY", "1")),
}


# ---------- 辅助函数 ----------
def build_message(from_addr: str, to_addr: str, subject_base: str, body_plain: str,
                  body_html: str, index: int, add_index: bool, identical_body: bool,
                  identical_message_id: Optional[str] = None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    subject = subject_base if not add_index else f"{subject_base} - #{index}"
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = "<mailto:unsubscribe@example.com>"  # 测试也放头提升信誉
    if identical_message_id:
        msg["Message-ID"] = identical_message_id

    if identical_body:
        plain = body_plain
        html = body_html
    else:
        plain = f"{body_plain}\n\n测试序号：{index}"
        html = f"{body_html}<p>测试序号：{index}</p>"

    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")
    return msg


def send_via_smtp(host: str, port: int, user: str, password: str,
                  message: EmailMessage, timeout: int = 60, use_starttls: bool = True,
                  login: bool = True) -> None:
    """
    发送单封邮件。可能抛出异常（调用者负责捕获并重试/处理）。
    """
    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        smtp.ehlo()
        if use_starttls:
            try:
                smtp.starttls()
                smtp.ehlo()
            except Exception:
                # 某些 SMTP 服务器（例如本地测试）可能不支持 STARTTLS
                pass
        if login and user and password:
            smtp.login(user, password)
        smtp.send_message(message)


# ---------- CLI 主流程 ----------
def main(argv=None):
    p = argparse.ArgumentParser(prog="send_smtp_cli", description="SMTP 重复发送测试工具（用于合规测试）")
    p.add_argument("--smtp-host", default=DEFAULTS["SMTP_HOST"], help="SMTP 服务器地址")
    p.add_argument("--smtp-port", type=int, default=DEFAULTS["SMTP_PORT"], help="SMTP 端口")
    p.add_argument("--smtp-user", default=DEFAULTS["SMTP_USER"], help="SMTP 用户名（发件人）")
    p.add_argument("--smtp-pass", default=DEFAULTS["SMTP_PASS"], help="SMTP 密码（或 app password）")
    p.add_argument("--to", default=DEFAULTS["TO_EMAIL"], help="收件人（默认发给自己）")
    p.add_argument("--count", type=int, default=DEFAULTS["SEND_COUNT"], help="发送次数")
    p.add_argument("--delay", type=float, default=DEFAULTS["DELAY_SEC"], help="每次发送后的延迟（秒）")
    p.add_argument("--subject", default=DEFAULTS["SUBJECT_BASE"], help="邮件主题基础文本")
    p.add_argument("--body-plain", default=DEFAULTS["BODY_PLAIN"], help="纯文本正文")
    p.add_argument("--body-html", default=DEFAULTS["BODY_HTML"], help="HTML 正文")
    p.add_argument("--no-subject-index", dest="subject_index", action="store_false",
                   help="不要在主题中加入序号（默认会加入）")
    p.add_argument("--identical-body", action="store_true", default=DEFAULTS["IDENTICAL_BODY"],
                   help="让每封邮件正文完全相同（默认 false，会包含序号以便区分）")
    p.add_argument("--identical-message-id", default="", help="可选：设置相同 Message-ID（大多不推荐）")
    p.add_argument("--dry-run", action="store_true", help="仅打印将要发送的邮件，不实际发送")
    p.add_argument("--use-mailhog", action="store_true",
                   help="使用本地 MailHog（会自动切换 host=localhost, port=1025, 不登录）")
    p.add_argument("--timeout", type=int, default=DEFAULTS["TIMEOUT"], help="SMTP 连接超时（秒）")
    p.add_argument("--retry", type=int, default=DEFAULTS["RETRY"], help="每封邮件失败时重试次数（默认1）")
    p.add_argument("--verbose", "-v", action="store_true", help="输出详细日志")
    args = p.parse_args(argv)

    # 如果使用 MailHog：覆盖 host/port 并禁用登录
    use_login = True
    smtp_host = args.smtp_host
    smtp_port = args.smtp_port
    if args.use_mailhog:
        smtp_host = "localhost"
        smtp_port = 1025
        use_login = False
        if args.verbose:
            print("[INFO] MailHog 模式：连接 localhost:1025，跳过登录。")

    # 校验最基础参数
    if not args.dry_run and use_login:
        if not args.smtp_user or not args.smtp_pass:
            print("错误：未配置 SMTP 用户或密码（非 dry-run 模式下必须）。可通过环境变量或 --smtp-user/--smtp-pass 提供。")
            sys.exit(1)

    print(f"准备发送到 {args.to}，次数 {args.count}，间隔 {args.delay}s（dry-run={args.dry_run}）。")
    for i in range(1, args.count + 1):
        msg = build_message(
            from_addr=(args.smtp_user or args.smtp_user),
            to_addr=args.to,
            subject_base=args.subject,
            body_plain=args.body_plain,
            body_html=args.body_html,
            index=i,
            add_index=args.subject_index,
            identical_body=args.identical_body,
            identical_message_id=(args.identical_message_id or None)
        )

        if args.dry_run:
            print(f"\n--- DRY RUN: [{i}/{args.count}] ---")
            print(f"Subject: {msg['Subject']}")
            print(f"From: {msg['From']}  To: {msg['To']}")
            print("Plain body preview:")
            print(msg.get_content())  # note: simple preview for plain part
            continue

        attempt = 0
        while attempt < max(1, args.retry):
            attempt += 1
            try:
                send_via_smtp(
                    host=smtp_host,
                    port=smtp_port,
                    user=args.smtp_user,
                    password=args.smtp_pass,
                    message=msg,
                    timeout=args.timeout,
                    use_starttls=not args.use_mailhog,
                    login=use_login
                )
                print(f"[{i}/{args.count}] 已发送（主题: {msg['Subject']}）")
                break
            except Exception as e:
                print(f"[{i}/{args.count}] 第 {attempt} 次发送失败: {e}")
                if attempt >= args.retry:
                    print(f"[{i}/{args.count}] 超过重试次数，跳到下一封。")
                else:
                    backoff = 1.0 * attempt
                    print(f"等待 {backoff}s 后重试...")
                    time.sleep(backoff)
        # 延迟（最后一次发送后不需要再等待）
        if i != args.count:
            time.sleep(args.delay)

    print("全部任务完成。")


if __name__ == "__main__":
    main()

