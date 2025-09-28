#!/usr/bin/env python3
"""
send_smtp.py
SMTP repeat send test script.

Usage:
  - Fill .env (or set environment variables).
  - python send_smtp.py
"""

import os
import time
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()  # will read .env if present

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

FROM = SMTP_USER
TO = os.getenv("TO_EMAIL", SMTP_USER)

SUBJECT_BASE = os.getenv("SUBJECT_BASE", "测试邮件 — 来自我的网站")
BODY_PLAIN = os.getenv("BODY_PLAIN", "这是测试邮件（纯文本）。")
BODY_HTML = os.getenv("BODY_HTML", "<p>这是测试邮件（HTML）。</p>")

# controls
SEND_COUNT = int(os.getenv("SEND_COUNT", "5"))
DELAY_SEC = float(os.getenv("DELAY_SEC", "2"))
SUBJECT_ADD_INDEX = os.getenv("SUBJECT_ADD_INDEX", "true").lower() in ("1","true","yes","y")
IDENTICAL_BODY = os.getenv("IDENTICAL_BODY", "false").lower() in ("1","true","yes","y")

# optional: set an idempotency token or message-id to be identical (rarely needed)
IDENTICAL_MESSAGE_ID = os.getenv("IDENTICAL_MESSAGE_ID", "")

def build_message(index: int):
    msg = EmailMessage()
    msg["From"] = FROM
    msg["To"] = TO

    if SUBJECT_ADD_INDEX:
        msg["Subject"] = f"{SUBJECT_BASE} - #{index}"
    else:
        msg["Subject"] = SUBJECT_BASE

    # helpful headers for reputation even in tests
    msg["List-Unsubscribe"] = "<mailto:unsubscribe@example.com>"
    if IDENTICAL_MESSAGE_ID:
        msg["Message-ID"] = IDENTICAL_MESSAGE_ID

    # body: if identical required, don't include index in body
    if IDENTICAL_BODY:
        plain = BODY_PLAIN
        html = BODY_HTML
    else:
        plain = f"{BODY_PLAIN}\n\n测试序号：{index}"
        html = f"{BODY_HTML}<p>测试序号：{index}</p>"

    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")
    return msg

def send_one(msg: EmailMessage):
    import smtplib
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as s:
        s.ehlo()
        # 如果服务器支持 TLS，则升级
        try:
            s.starttls()
            s.ehlo()
        except Exception:
            # 有些内部 SMTP 可能不需要 starttls
            pass
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def main():
    if not SMTP_USER or not SMTP_PASS:
        print("错误：SMTP_USER 或 SMTP_PASS 未配置。请在 .env 中设置。")
        return

    print(f"开始发送：目标 {TO}，次数 {SEND_COUNT}，间隔 {DELAY_SEC}s。")
    for i in range(1, SEND_COUNT + 1):
        msg = build_message(i)
        try:
            send_one(msg)
            print(f"[{i}/{SEND_COUNT}] 已发送到 {TO}（主题: {msg['Subject']}）")
        except Exception as e:
            print(f"[{i}/{SEND_COUNT}] 发送失败: {e}")
        if i != SEND_COUNT:
            time.sleep(DELAY_SEC)
    print("发送完成。")

if __name__ == "__main__":
    main()

