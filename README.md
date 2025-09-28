# 📧 MailSending

一个使用 Python 编写的简单邮件发送工具。  
支持通过 **SMTP（Gmail / QQ 邮箱 / 其他邮箱服务商）** 发送邮件，并可设置发送次数与时间间隔。  
适用于学习、测试网页收件功能等场景（仅限合规使用）。

---

## 🚀 功能特性
- 支持 **Gmail App Password** / **QQ 邮箱授权码** 登录
- 配置化：使用 `.env` 文件存放邮箱账号、密码、收件人等信息（不会上传到仓库）
- 可设置 **发送次数** 和 **间隔时间**
- 支持 CLI 命令行输出，直观显示每次发送情况
- 安全：默认 `.gitignore` 忽略 `.env`，避免泄露敏感信息

---

## 📂 项目结构
```
MailSending/
├── smtp_sender.py       # 主脚本
├── requirements.txt     # 依赖
├── .gitignore           # 忽略文件（已包含 .env）
└── README.md            # 项目说明
```

---

## ⚙️ 环境准备

1. 克隆项目：
   ```bash
   git clone https://github.com/LuckyLivio/MailSending.git
   cd MailSending
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 在根目录下新建 `.env` 文件，写入邮箱配置：
   ```env
   # SMTP 配置
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=465
   SMTP_USER=yourname@gmail.com
   SMTP_PASS=abcdefghijklmnop   # Gmail App Password 或 QQ 授权码

   # 收件人（默认发给自己）
   TO_EMAIL=receiver@example.com

   # 发送控制
   SEND_COUNT=5
   DELAY_SEC=2
   ```

---

## 🔑 如何获取 Gmail 应用专用密码
1. 打开 Google 账号安全设置
2. 启用 两步验证 (2FA)
3. 在 “应用专用密码” 中新建一个 Mail 类型的密码
4. 获得 16 位密码（例如 abcd efgh ijkl mnop），去掉空格填入 `.env` 的 `SMTP_PASS`

---

## 📤 使用方法

运行脚本：
```bash
python smtp_sender.py
```

示例输出：
```
准备发送到 receiver@example.com，次数 5，间隔 2.0s
[1/5] 已成功发送
[2/5] 已成功发送
...
[5/5] 已成功发送
所有邮件发送完成！
```

---

## 📌 注意事项
- 切勿滥用：本工具仅用于 **学习 / 自测网页收件功能**，不要用于垃圾邮件发送，违规使用需自行承担法律责任。
- 邮箱权限配置：
  - 使用 Gmail 时，必须使用 **App Password**（普通账号密码无法登录 SMTP）
  - 使用 QQ 邮箱时，需先在账号设置中开启「SMTP/IMAP 服务」，再生成专属 **授权码**
- 常见错误排查：若出现 `(535, 'Username and Password not accepted')` 错误，大概率是密码/授权码错误，需重新检查 `.env` 中的 `SMTP_PASS` 是否为正确的 App Password 或授权码。

---

## 📜 License

本项目采用 **MIT License** 开源，允许个人及商业场景下的修改与使用（需保留原作者声明）。

---

## 👨‍💻 Author: LuckyLivio
