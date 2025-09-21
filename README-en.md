# `share-cli` - One-Click Deployment for Secure Single-File Sharing

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[简体中文](/README.md)

**`share-cli` is an extremely simple single-file HTTP server.** With just one Python script, you can quickly and securely share your folders within a local area network.

```bash
# Install using pipx (Highly Recommended)
pipx install share-cli

# Or install using pip
pip install --user share-cli
```

No dependencies to install, no complex configurations. Open your browser and start browsing, uploading, and playing your files instantly.

## 🌐 Use Cases

`share` is more than just a file transfer tool; it's a lightweight personal cross-device file and media center. Its core value lies in: **making information access simpler**. Often, you just need to quickly view or play a file, not go through the hassle of downloading it.

Here are some real and common usage scenarios:

### 🏠 Home Sharing
- **Share precious moments with family**: During weekend gatherings, you take lots of photos and videos on your Android device. Start `share` to share the photo folder, and family members can directly **swipe through high-resolution images** and **seamlessly play videos** on their phones, tablets, computers, or smart TV browsers—no waiting for downloads or transferring files between devices.
- **Create a home media library**: Share a folder containing movies and TV shows from your study computer. Open a browser on your living room tablet or laptop and **stream directly online** for a smooth viewing experience, eliminating the need to copy files. You can even download a movie on your phone, share it with `share`, and watch it on your tablet or computer.

### 👨‍🎓 Personal Multi-Device Synergy (Perfect for Students!)
- **Read papers vertically on your tablet, edit horizontally on your computer**: This is a killer feature for `share`. As a student, your computer holds PDFs, e-books, and study materials. After starting `share` on your computer, you can open the browser on your tablet for **immersive vertical reading of papers**, while freeing up your computer screen for focused literature review or coding, effectively doubling your study efficiency.
- **Temporarily check materials on your phone, easily share from your computer**: While researching on your computer, instead of sending files to WeChat, just open the `share` address on your phone browser to continue **browsing PDF documents from your computer** (export Word/PPT to PDF first).
- **Cross-device file transfer & preview**: Photos and videos taken on your phone can be **uploaded directly** to your computer's shared directory for quick backup and organization. Conversely, preview a video or image from your computer on your phone instantly without downloading.

### 📱 Quick, Temporary File Access
- **Need a file from your computer on your phone**: Share the directory containing the file from your computer and download it directly via your phone's browser—faster and more straightforward than finding a cable or logging into QQ/WeChat file transfer.
- **Temporarily grab a file from another computer**: Share files from your dorm computer and download them from the lab computer (if you can get the IP)—secure and convenient.

**In short, `share` simplifies complexity, instantly turning your personal computer into a lightweight server focused on "access" rather than "management." It builds a seamless bridge between your phone, tablet, and computer, making the flow of information within your local network more direct and efficient than ever before.**

## 🚀 Why Choose `share`?

### ✅ Single File, Extremely Simple
- **One file is all you need**: The entire project is just a `share.py` script—no complex directory structure.
- **Zero dependencies**: Relies only on the Python standard library. Run it anytime, anywhere there's a Python environment.
- **One-click deployment**: Download the script, run it from the command line, and you're done in 3 seconds.

### 🔐 Security-First Design Philosophy
We understand the importance of data security. `share`'s design philosophy is: **maximize convenience while minimizing risk**.

- **No destructive operations**: `share` **does not provide** file deletion, renaming, or moving capabilities.
    - **Why?** This is an **intentional security design**. In an open LAN environment, any modification operation could be misused or accidentally executed, leading to irreversible data loss. `share` focuses on "**secure sharing**," ensuring your original data remains safe.
- **Optional access control**:
    - **Password protection**: Use the `--password` parameter to add an access barrier.
    - **HTTPS encryption**: Use the `--https` parameter to enable HTTPS encrypted transmission, preventing data from being intercepted or tampered with on the local network. Note: After enabling, browsers will show an "invalid certificate" warning because a self-signed certificate is used. This is normal; please click "Advanced" -> "Proceed anyway". This warning does not affect the effectiveness of the encryption; it still effectively protects against sniffing attacks on the LAN.

### 🌟 Powerful and Smooth Experience
Despite its simple design, its features are uncompromising:
- **Paginated browsing**: Easily browse through thousands of files with fast loading. (The first load for directories with many files might be slow, but it's fast afterward with caching.)
- **Multimedia center**: Built-in image, audio, and video players with support for swipe gestures/arrow keys to navigate; press ESC to exit.
- **Text highlighting**: Syntax highlighting for code and text files for more comfortable reading; supports arrow key navigation and ESC to exit.
- **Drag-and-drop upload**: Drag files directly into the browser to upload them to the currently browsed directory, just like a local file manager.
- **One-click download**: Click a file in the list to download it, or right-click to save as. (Currently supports file upload/download only, not folders.)

## ⚠️ Security Warning

`share` is designed for use in **trusted local network environments** (like home or office).
- **Avoid exposure to the public internet**: Do not expose this server to the internet, as it lacks enterprise-grade security audits and user management.
- **HTTPS is key**: When using it on an insecure network (like public WiFi), **strongly enable `--https`** to encrypt your data transmission.
- **Password protection**: In multi-user environments, use `--password` to prevent unauthorized access.

## 🚀 Quick Start

### 📦 Installation & Deployment

> **Say goodbye to manual script downloads! You can now install `share` with a single command using standard Python package managers.**

#### 1: Install the `share-cli` Command Line Tool

> **Recommended: Install seamlessly via PyPI, no manual file downloads required.**

You have two recommended installation methods:

**Method 1: Install using `pipx` (Highly Recommended)**

`pipx` is designed specifically for installing Python command-line tools. It creates an isolated virtual environment for `share`, avoiding pollution of your main Python environment.

```bash
# Install pipx (if not already installed)
pip install pipx
pipx ensurepath

# Use pipx to install share from PyPI
pipx install share-cli
```

**Method 2: Install using `pip`**

If you prefer not to use `pipx`, you can install directly with `pip`:

```bash
pip install --user share-cli
```

> ✅ **After installation, you can use the `share` command from anywhere in your terminal!**
>
> `Android` users can also use the above `pip` command to install after installing `python` via `termux`.

---

#### (Optional) Manual Download and Installation

If you want to manually download the wheel file for installation:

1.  Visit the project's [Gitee Release page](https://gitee.com/jackiehankk/share/releases) or [GitHub Releases page](https://github.com/jackiehank/share/releases).
2.  Under the latest release (e.g., `v0.4.6`), find the **Assets** section.
3.  Download the file `share_cli-0.4.6-py3-none-any.whl`.
4.  Install the downloaded file using `pipx` or `pip`:

```bash
# Using pipx
pipx install ./share_cli-0.4.6-py3-none-any.whl

# Or using pip
pip install --user ./share_cli-0.4.6-py3-none-any.whl
```

#### 2: Start Using It!

Once installed, you can use the `share` command from anywhere in your terminal!

```bash
# Share the current directory
share .

# Share a specified folder on a specified port
share /path/to/your/folder -p 8080

# Enable password protection
share ~/Documents --password

# Enable HTTPS encryption (requires openssl; not required if not enabling HTTPS)
share ~/Pictures --https
```

#### 3. Access the Share

After the server starts, it will display the access address, for example:
```
Serving HTTP on 0.0.0.0 port 8000 (http://192.168.0.10:8000/)
```
Open a browser on any other device within the local network and visit this address.

## 🛠 Usage

```bash
usage: share [-h] [--password] [--https] [--cert CERT] [--key KEY] [-p PORT] [--host HOST] folder

Positional Arguments:
  folder                Path to the folder to share

Optional Arguments:
  --password            Enable password protection
  --https               Enable HTTPS (auto-generates self-signed certificate)
  --cert CERT           Custom HTTPS certificate file path
  --key KEY             Custom HTTPS private key file path
  -p PORT, --port PORT  Server port (default: 8000)
  --host HOST           Host address to bind to (default: 0.0.0.0)
```

## 🤝 Contributing

Welcome to report issues or make suggestions via Issues.

## 📄 License

MIT