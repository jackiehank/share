# `share` - 一键部署的单文件安全文件共享

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**`share` 是一个极致简单的单文件 HTTP 服务器。** 只需一个 Python 脚本，即可在局域网内快速、安全地共享您的文件夹。

```bash
# 1. 下载脚本
wget https://github.com/jackiehank/share/raw/main/share.py

# 2. 一键运行！
python3 share.py /path/to/your/folder
```

无需安装依赖，无需复杂配置。打开浏览器，即刻开始浏览、上传和播放您的文件。

## 🚀 为什么选择 `share`？

### ✅ 单文件，极致简洁
- **一个文件就是全部**：整个项目就是一个 `share.py` 脚本，没有复杂的目录结构。
- **零依赖**：仅依赖 Python 标准库，只要有 Python 环境，随时随地都能运行。
- **一键部署**：下载脚本，命令行运行，3 秒完成部署。

### 🔐 安全优先的设计理念
我深知数据安全的重要性。`share` 的设计哲学是：**在提供便利的同时，最大限度地降低风险**。

- **无破坏性操作**：`share` **不提供**文件删除、重命名或移动功能。
    - **为什么？** 这是**刻意为之的安全设计**。在开放的局域网环境中，任何修改操作都可能被滥用或误操作，导致不可逆的数据丢失。`share` 专注于“**安全共享**”，确保您的原始数据万无一失。
- **可选的访问控制**：
    - **密码保护**：使用 `--password` 参数，为您的共享添加一道访问屏障。
    - **HTTPS 加密**：使用 `--https` 参数，启用 HTTPS 加密传输，防止数据在局域网内被窃听或篡改。注意：启用后浏览器会提示“证书无效”，这是因为使用的是自签名证书。这是正常现象，请点击“高级” -> “继续访问”即可。此警告不影响加密的有效性，它依然能有效抵御局域网内的嗅探攻击。

### 🌟 强大而流畅的体验
尽管设计简洁，但功能毫不妥协：
- **分页浏览**：轻松浏览成千上万个文件，加载飞快。(包含大量文件的目录第一次加载较慢，之后有缓存就很快了)
- **多媒体中心**：内置图片、音视频播放器，支持滑动手势/方向键切换，ESC退出。
- **文本高亮**：代码、文本文件语法高亮显示，阅读更舒适；支持方向键切换，ESC退出。
- **拖拽上传**：将文件直接拖入浏览器即可上传到当前浏览目录，就像本地文件管理器一样方便。
- **一键下载**：点击文件列表中的文件即可下载，或者右键另存为。(目前只提供文件上传下载，不提供文件夹上传下载)

## ⚠️ 安全警告

`share` 设计用于**受信任的局域网环境**（如家庭、办公室）。
- **避免暴露在公网**：请勿将此服务器暴露在互联网上，因为它不包含企业级的安全审计和用户管理。
- **HTTPS 是关键**：当在不安全的网络（如公共WiFi）中使用时，**强烈建议启用 `--https`** 来加密您的数据传输。
- **密码保护**：在多用户环境中，使用 `--password` 防止未授权访问。

## 🚀 快速开始

### 📦 安装与部署

> **告别手动下载脚本！现在，你可以通过标准的 Python 包管理器一键安装 `share`。**

`share` 已被打包为标准的 Python wheel 文件（`.whl`），你可以从 GitHub Release 页面下载并安装，享受更稳定、更便捷的体验。

#### 1: 下载安装包

1.  访问项目的 [Releases 页面](https://github.com/jackiehank/share/releases)。
2.  在最新的版本（如 `v0.4.3`）下，找到 **Assets** 部分。
3.  下载文件 `share-0.4.3-py3-none-any.whl`。

#### 2: 安装

你有两种推荐的安装方式：

**方式一：使用 `pipx` 安装（强烈推荐）**

`pipx` 是专为安装 Python 命令行工具设计的工具，它会为 `share` 创建一个独立的虚拟环境，避免污染你的主 Python 环境。

```bash
# 安装 pipx (如果尚未安装)
pip install pipx
pipx ensurepath

# 使用 pipx 安装 share
pipx install ./share-0.4.3-py3-none-any.whl
```

**方式二：使用 `pip` 安装**

如果你不想使用 `pipx`，也可以直接用 `pip` 安装：

```bash
pip install --user ./share-0.4.3-py3-none-any.whl
```

#### 3: 开始使用！

安装完成后，你就可以在终端的任何位置使用 `share` 命令了！

```bash
# 共享当前目录
share .

# 共享指定文件夹、指定端口
share /path/to/your/folder -p 8080

# 启用密码保护
share ~/Documents --password

# 启用HTTPS加密(依赖 openssl，不启用则无需安装)
share ~/Pictures --https
```

#### 4. 访问共享

服务器启动后，会显示访问地址，例如：
```
Serving HTTP on 0.0.0.0 port 8000 (http://192.168.1.10:8000/)
```
在局域网内的其他设备上，打开浏览器访问该地址即可。

## 🛠 使用方法

```bash
usage: share [-h] [--password] [--https] [--cert CERT] [--key KEY] [-p PORT] [--host HOST] folder

位置参数:
  folder                要共享的文件夹路径

可选参数:
  --password            启用密码保护
  --https               启用HTTPS（自动生成自签名证书）
  --cert CERT           自定义HTTPS证书文件路径
  --key KEY             自定义HTTPS私钥文件路径
  -p PORT, --port PORT  服务器端口 (默认: 8000)
  --host HOST           监听地址 (默认: 0.0.0.0)
```

## 🤝 贡献

欢迎通过 Issues 报告问题或提出建议。

## 📄 许可证

MIT
