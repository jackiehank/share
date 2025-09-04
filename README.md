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
- **一键部署**：下载脚本，双击或命令行运行，3 秒完成部署。

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

### 1. 获取脚本

```bash
# 下载单个文件
curl -O https://raw.githubusercontent.com/jackiehank/share/main/share.py
```

### 2. 一键部署 (推荐)

为了让使用更加便捷，您可以创建一个启动脚本，使其像一个系统命令一样工作。

#### 在 Linux/macOS 上

1.  将脚本重命名为 `share` (去掉 `.py` 后缀)。
2.  添加可执行权限。
3.  （可选）将其移动到 `PATH` 中的目录，如 `~/bin`。

```bash
# 1. 重命名并赋予可执行权限
mv share.py share
chmod +x share

# 2. 移动到用户.local/bin目录（如果存在）
mkdir -p ~/.local/bin
mv share ~/.local/bin/

# 3. 确保 ~/.local/bin 在你的 PATH 环境变量中
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

之后，您就可以在任何地方直接使用 `share` 命令了：
```bash
share ~/Downloads --password
```

#### 在 Windows 上

1.  使用 `share.bat` 批处理文件，与 `share` 脚本放在同一目录。

**`share.bat` 文件内容：**
```batch
@echo off
python "%~dp0share.py" %*
```

这个批处理文件会调用当前目录下的 `share` 脚本，并将所有参数传递给它。

之后，您就可以在命令提示符或 PowerShell 中，进入脚本所在目录，然后直接运行：
```cmd
share C:\Users\YourName\Pictures --https
```

### 3. 手动运行

您也可以直接使用 Python 运行：

```bash
# 共享当前目录
python3 share.py .

# 共享指定文件夹
python3 share.py /path/to/your/folder -p 8080

# 启用密码保护
python3 share.py ~/Documents --password

# 启用HTTPS加密
python3 share.py ~/Pictures --https
```

### 4. 访问共享

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

## 📂 项目结构

```bash
share/
├── share.py      # 核心脚本，单文件，开箱即用
├── share.bat     # Windows 系统启动脚本
├── README.md     # 本文件
└── LICENSE       # MIT 许可证
```

## 🔧 配置说明

`share` 提供了灵活的配置选项，您可以通过修改脚本开头的常量定义来自定义服务器的行为，而无需修改核心代码。

### SSL 配置

```python
SSL_DIR = os.path.expanduser("~/.config/share/ssl")  # SSL证书存储目录
CERT_FILE = os.path.join(SSL_DIR, "certificate.crt")  # 证书文件路径
KEY_FILE = os.path.join(SSL_DIR, "private.key")       # 私钥文件路径
```

**修改建议**：
- 可以更改 `SSL_DIR` 来指定自定义的证书存储位置
- 如果已有证书和私钥，可以直接修改 `CERT_FILE` 和 `KEY_FILE` 路径指向现有文件

### 分页和缓存配置

```python
ITEMS_PER_PAGE = 100    # 每页显示的文件和目录数量
CACHE_CAPACITY = 2000   # 缓存最大容量（项目数）
CACHE_TIMEOUT = 36000   # 缓存超时时间（秒），默认10小时
```

**修改建议**：
- 对于包含大量文件的目录，可以适当增加 `ITEMS_PER_PAGE` 值（但可能影响加载性能）
- 在内存受限的环境中，可以减小 `CACHE_CAPACITY`
- 对于频繁变动的目录，可以减小 `CACHE_TIMEOUT` 以确保内容及时更新

### 文件类型支持配置

脚本预定义了多种文件类型的扩展名，您可以根据需要添加或删除：

### 图片格式
```python
IMAGE_EXTENSIONS = {...}
```

### 视频格式
```python
VIDEO_EXTENSIONS = {...}
```

### 音频格式
```python
AUDIO_EXTENSIONS = {...}
```

### 文本/代码格式
```python
TEXT_EXTENSIONS = {...}
```

### 常见文本文件名称（无扩展名）
```python
COMMON_TEXT_FILES = {...}
```

**修改建议**：
- 根据您的需求添加或删除特定的文件扩展名
- 对于图片、视频、音频，只要点击文件链接可以使用浏览器查看的格式，都可以添加
- 添加新格式后，相应的文件将获得特殊的查看/播放界面
- 对于文本格式，都可以添加到`TEXT_EXTENSIONS`

## 应用配置更改

修改这些常量后，只需重启 `share` 服务器即可应用更改：

```bash
# 停止当前服务器 (Ctrl+C)
# 重新启动
python share.py /path/to/folder
```

这些配置选项使您能够精细调整服务器行为，而无需理解或修改复杂的内部逻辑。

## 🤝 贡献

欢迎通过 Issues 报告问题或提出建议。

## 📄 许可证

MIT
