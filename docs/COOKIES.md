# YouTube Cookie 导出指南

当 YouTube 检测到自动化请求时，需要使用 cookie 进行认证。本指南将帮助您导出 cookie 文件。

## 方法 1: 使用浏览器扩展（推荐，最简单）

### Chrome/Edge

1. **安装 "Get cookies.txt" 扩展**
   - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbanldfjnne
   - Edge: https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locally/jeopekbbikhmbmjdjbmngploabpbgkfp

2. **导出 YouTube Cookie**
   - 打开 YouTube 并登录
   - 点击扩展图标
   - 选择 "Current Site"
   - 点击 "Export" 导出为 `cookies.txt`

3. **使用**
   ```bash
   python main.py --search "Quantum Computing 101" --cookies-file cookies.txt
   ```

### Firefox

1. **安装 "cookies.txt" 扩展**
   - https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. **导出步骤同上**

---

## 方法 2: 使用 yt-dlp 内置功能（无需浏览器扩展）

如果您已经安装 yt-dlp，可以直接使用其命令行工具导出 cookie：

```bash
# 从 Chrome 导出（需要关闭 Chrome）
yt-dlp --cookies-from-browser chrome --print-cookies > cookies.txt

# 从 Firefox 导出
yt-dlp --cookies-from-browser firefox --print-cookies > cookies.txt
```

---

## 方法 3: 手动导出（高级）

### Windows Chrome

1. **安装 SQLite 浏览器**
   - 下载: https://sqlitebrowser.org/dl/

2. **找到 Cookie 数据库**
   - 路径: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cookies`

3. **复制数据库**（Chrome 运行时无法直接访问）
   - 关闭 Chrome
   - 复制 Cookies 文件到其他位置

4. **使用 SQLite 浏览器打开**

5. **导出为 Netscape 格式**
   - 选择需要的 cookie（主要是 `.youtube.com` 和 `google.com` 域名）
   - 文件 → 导出 → Netscape Cookie 格式

---

## Cookie 文件格式

Netscape cookie 文件格式示例：

```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	FALSE	1735689600	SID	<your_session_id>
.youtube.com	TRUE	/	FALSE	1735689600	HSID	<your_session_id>
.youtube.com	TRUE	/	FALSE	1735689600	SSID	<your_session_id>
.youtube.com	TRUE	/	TRUE	0	PREF	<your_pref>
.google.com	TRUE	/	FALSE	1735689600	SID	<your_session_id>
```

**关键字段说明：**
- 第 1 列: 域名
- 第 2 列: 是否包含所有子域 (TRUE/FALSE)
- 第 3 列: 路径
- 第 4 列: 是否仅安全连接 (TRUE/FALSE)
- 第 5 列: 过期时间（Unix 时间戳）
- 第 6 列: Cookie 名称
- 第 7 列: Cookie 值

---

## 使用方法

将导出的 `cookies.txt` 文件放在项目目录下，然后运行：

```bash
# 搜索视频
python main.py --search "Quantum Computing 101" --cookies-file cookies.txt

# 下载视频
python main.py --url <VIDEO_URL> --cookies-file cookies.txt
```

---

## 注意事项

1. **安全性**: Cookie 文件包含您的登录信息，请勿分享给他人
2. **有效期**: Cookie 通常会过期，如果失效请重新导出
3. **隐私**: 建议定期更换 cookie 并在使用后删除本地文件
4. **YouTube 账号**: 确保导出 cookie 时已登录 YouTube

---

## 故障排除

### Q: 导出后仍然提示认证失败
A: Cookie 可能已过期，请重新登录 YouTube 并导出

### Q: Chrome 数据库被锁定
A: 完全关闭 Chrome（包括后台进程），或使用 Firefox/浏览器扩展方法

### Q: 不确定哪些 cookie 是必需的
A: 使用浏览器扩展自动导出最可靠，它会选择正确的 cookie
