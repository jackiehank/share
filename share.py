#!/usr/bin/env python3
"""
HTTP文件服务器 - 支持分页浏览、图片查看和媒体播放功能

这是一个HTTP文件服务器，专门设计用于在局域网内共享文件。它提供了现代化的Web界面，
支持分页浏览大量文件、上传文件、图片查看、视频和音频播放，以及文本文件的高亮显示。

主要功能:
- 分页浏览文件和目录（每页100个项目）
- 点击上传按钮上传文件、直接拖放上传文件到当前浏览目录
- 图片查看器，支持缩略图浏览和全屏查看
- 视频和音频播放器，支持播放列表和连续播放
- 图片、视频、音频、代码查看页在PC端可以使用方向键切换
- 图片、视频、音频查看页在移动端可以使用手势切换
- 文本文件查看器，支持语法高亮和代码换行
- 智能缓存机制，提升大量文件的加载性能
- 响应式设计，支持桌面和移动设备
- 支持Range请求，优化大文件传输
- 可选的HTTPS支持，使用自签名证书

使用方法:
  share [文件夹路径] [选项]

参数:
  folder      要提供服务的文件夹路径（必需）

选项:
  --password                设置访问密码（默认: 无密码）
  --https                   启用 HTTPS（自动生成自签名证书）
  --cert CERT               HTTPS 证书文件路径（.crt 或 .pem）
  --key KEY                 HTTPS 私钥文件路径（.key）
  -p,--port PORT            服务器端口（默认: 8000）
  --host HOST               服务器监听地址（默认: 0.0.0.0 - 所有网络接口）
  --debug-cache             在页面底部显示缓存统计信息
  --cache-timeout TIMEOUT   缓存超时时间（秒）（默认: 36000）
  --cache-capacity CAPACITY 缓存最大容量（默认: 2000）

示例:
  # 服务当前目录，使用默认端口8000
  share .

  # 服务指定目录，使用自定义端口8080
  share /path/to/folder -p 8080

  # 在所有网络接口上服务，启用缓存调试信息
  share /shared/folder --host 0.0.0.0 --debug-cache

访问方式:
  启动后，可以通过以下方式访问:
  - 本地访问: http://localhost:端口号
  - 局域网访问: http://本机IP:端口号

特殊端点:
  - /cache-stats: 查看缓存统计信息
  - /cache-clear: 清空缓存
  - /cache-config: 配置缓存参数（需提供timeout和capacity参数）

支持的媒体格式:
  - 图片: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg, .tiff, .ico, .avif等
  - 视频: .mp4, .avi, .mov, .mkv, .webm, .flv, .wmv, .m4v, .3gp等
  - 音频: .mp3, .wav, .ogg, .m4a, .flac
  - 文本: 多种编程语言和文本文件扩展名
  - 后续可以在常量定义中添加更多扩展名

注意事项:
  1. 确保有读取目标文件夹的权限
  2. 大文件传输可能会受到python内置HTTP服务器的限制
  3. 视频播放需要浏览器支持HTML5 video标签

缓存机制:
  服务器使用LRU（最近最少使用）缓存算法来存储目录列表，显著提升包含大量文件的目录的加载速度。
  缓存默认超时时间为36000秒（10小时），最大容量为2000个项目。

退出方式:
  按Ctrl+C可停止服务器

"""

__version__ = "0.4.7"
__author__ = "Jackie Hank"
__license__ = "MIT"

import argparse
import base64
import getpass
import json
import os
import platform
import socket
import socketserver
import ssl
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from html import escape
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, quote, unquote, urlparse
import logging
from logging.handlers import RotatingFileHandler
import platform
import os


# 常量定义
# 日志配置常量
LOG_FILE_NAME = "share.log"

# SSL 配置
SSL_DIR = os.path.expanduser("~/.config/share/ssl")
CERT_FILE = os.path.join(SSL_DIR, "certificate.crt")
KEY_FILE = os.path.join(SSL_DIR, "private.key")

# 分页和缓存配置
ITEMS_PER_PAGE = 100  # 每页显示的文件和目录数量
CACHE_CAPACITY = 2000  # 缓存最大容量
CACHE_TIMEOUT = 36000  # 缓存超时时间（秒）

# 支持的文件扩展名
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".tiff",
    ".ico",
    ".avif",
    ".jfif",
    ".pjpeg",
    ".pjp",
    ".heic",
    ".heif",
}
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".m4v",
    ".3gp",
}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".xml",
    ".csv",
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".go",
    ".rs",
    ".js",
    ".css",
    ".sh",
    ".bat",
    ".log",
    ".yml",
    ".yaml",
    ".toml",
    ".asm",
    ".htm",
    ".php",
    ".rb",
    ".pl",
    ".pm",
    ".lua",
    ".sql",
    ".ini",
    ".conf",
    ".cfg",
    ".properties",
    ".tex",
    ".rst",
    ".asciidoc",
    ".adoc",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".sass",
    ".scss",
    ".less",
    ".styl",
    ".stylus",
    ".coffee",
    ".clj",
    ".cljs",
    ".cljc",
    ".edn",
    ".scala",
    ".kt",
    ".kts",
    ".dart",
    ".elm",
    ".erl",
    ".hrl",
    ".ex",
    ".exs",
    ".fs",
    ".fsx",
    ".fsi",
    ".ml",
    ".mli",
    ".hs",
    ".purs",
    ".v",
    ".sv",
    ".vhd",
    ".vhdl",
    ".tcl",
    ".awk",
    ".sed",
    ".nim",
    ".zig",
    ".odin",
    ".v",
    ".f",
    ".f90",
    ".f95",
    ".f03",
    ".f08",
    ".m",
    ".mm",
    ".r",
    ".rmd",
    ".swift",
    ".groovy",
    ".gradle",
    ".jsp",
    ".asp",
    ".aspx",
    ".jspx",
    ".cs",
    ".csx",
    ".vb",
    ".vbs",
    ".ps1",
    ".psm1",
    ".psd1",
    ".ps1xml",
    ".pssc",
    ".cdxml",
    ".xaml",
    ".axaml",
    ".resx",
    ".config",
    ".csproj",
    ".vbproj",
    ".fsproj",
    ".sln",
    ".suo",
    ".gitignore",
    ".gitattributes",
    ".dockerfile",
    ".makefile",
    ".cmake",
    ".mk",
    ".ipynb",
    ".markdown",
    ".mdown",
    ".mkd",
    ".mkdn",
    ".mkdown",
    ".mdwn",
    ".lock",
    ".mod",
    ".sum",
    ".ini",
    ".cfg",
    ".conf",
    ".properties",
    ".lean",
}
COMMON_TEXT_FILES = {
    "readme",
    "license",
    "changelog",
    "contributing",
    "authors",
    "makefile",
    "dockerfile",
}

CSS_STYLES = """
<style>
    :root {
    --move-threshold: 80px; 
    --thumbnail-size: 410px;
    --thumbnail-gap: 10px;
    --color-primary: #007BFF;
    --color-primary-dark: #0056b3;
    --color-white: white;
    --color-black: black;
    --color-gray-light: #f0f0f0;
    --color-gray-medium: #e0e0e0;
    --color-gray-text: #333;
    --color-gray-subtext: #666;
    --color-gray-bg: #f9f9f9;
    --color-border: #ccc;
    --color-shadow: rgba(0, 0, 0, 0.1);
    --color-overlay: rgba(0, 0, 0, 0.9);


    --color-primary: #2D6FF7;
    --color-primary-dark: #1A56C2;
    --color-primary-light: #E0EBFF;
    --color-white: #ffffff;
    --color-black: #1A1A1A;
    --color-gray-50: #F9FAFB;
    --color-gray-100: #F3F4F6;
    --color-gray-200: #E5E7EB;
    --color-gray-300: #D1D5DB;
    --color-gray-400: #9CA3AF;
    --color-gray-500: #6B7280;
    --color-gray-600: #4B5563;
    --color-gray-700: #374151;
    --color-gray-800: #1F2937;
    --color-gray-900: #111827;
    --color-success: #10B981;
    --color-warning: #F59E0B;
    --color-error: #EF4444;
    --border-radius: 8px;
    --border-radius-sm: 4px;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --transition: all 0.2s ease;
    }

    body { font-family: sans-serif; padding: 0.5em; margin: 0; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 0.5em; border-bottom: 1px solid var(--color-border); }
    th:nth-child(1), td:nth-child(1) { width: 80%; }  /* 名称列占80% */
    th:nth-child(2), td:nth-child(2) { width: 20%; }  /* 大小列占20% */
    tr:hover { background-color: var(--color-gray-50); }

    .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--color-gray-200);
    }

    .container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 0.5rem;
    box-sizing: border-box;
    }

    h1 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--color-gray-900);
    }

    .view-options {
    display: flex;
    gap: 0.5rem;
    }

    .view-btn {
    padding: 0.5rem 1rem;
    background: var(--color-white);
    color: var(--color-gray-700);
    border: 1px solid var(--color-gray-300);
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 0.375rem;
    }

    .view-btn:hover {
    background: var(--color-gray-100);
    border-color: var(--color-gray-400);
    }

    .view-btn.active {
    background: var(--color-primary-light);
    color: var(--color-primary);
    border-color: var(--color-primary);
    }

    /* 文件名允许换行 */
    .filename-cell {
    word-wrap: break-word;      /* 允许长单词换行 */
    word-break: break-all;      /* 强制换行 */
    white-space: normal;        /* 允许换行 */
    }

    .filename-cell {
    word-wrap: break-word;
    word-break: break-word;
    white-space: normal;
    }

    .filename-cell a {
    color: var(--color-gray-900);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: var(--transition);
    }

    .filename-cell a:hover {
    color: var(--color-primary);
    }

    .filename-cell a::before {
    content: '';
    display: inline-block;
    width: 1.5rem;
    height: 1.5rem;
    background-size: contain;
    background-repeat: no-repeat;
    flex-shrink: 0;
    }

    .filename-cell a[href$="/"]::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236B7280'%3E%3Cpath d='M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z'/%3E%3C/svg%3E");
    }

    .filename-cell a:not([href$="/"])::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236B7280'%3E%3Cpath d='M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z'/%3E%3C/svg%3E");
    }

    .file-size {
    color: var(--color-gray-600);
    font-feature-settings: 'tnum';
    font-variant-numeric: tabular-nums;
    }

    .pagination { margin-top: 1em; }
    .pagination a,button { margin: 0 0.2em; text-decoration: none; color: var(--color-primary); }
    .pagination strong { margin: 0 0.2em; }
    .ellipsis { margin: 0 0.25em;padding: 0.5em 0;color: var(--color-gray-subtext); }

    .pagination { margin-top: 1.5em; text-align: center; }
    .pagination a, .pagination strong,button { display: inline-block; margin: 0 0.25em; padding: 0.5em 0.75em; text-decoration: none; border-radius: 4px; }
    .pagination a,button { background-color: var(--color-gray-light); color: var(--color-gray-text); }
    .pagination a:hover,button:hover { background-color: var(--color-gray-medium); }
    .pagination strong { background-color: var(--color-primary); color: var(--color-white); }

    /* 上传相关样式 */
    .upload-container {
        position: relative;
        display: inline-block;
    }

    .upload-progress {
        position: fixed;
        top: 10px;
        right: 10px;
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        min-width: 200px;
        max-width: 300px;
        display: none;
    }

    .progress-item {
        margin-bottom: 8px;
        font-size: 14px;
    }

    .progress-item:last-child {
        margin-bottom: 0;
    }

    .progress-filename {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 4px;
    }

    .progress-bar-container {
        height: 4px;
        background: #f0f0f0;
        border-radius: 2px;
        overflow: hidden;
    }

    .progress-bar-fill {
        height: 100%;
        background: var(--color-primary);
        transition: width 0.3s ease;
    }

    .drag-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 999;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .drag-overlay.active {
        opacity: 1;
    }

    .drag-message {
        background: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        font-size: 18px;
    }

    /* 桌面端保持正常表格样式 */
    @media (min-width: 601px) {
        th, td { display: table-cell; }
    }

    /* 移动端紧凑显示 */
    @media (max-width: 600px) {
        body { padding: 0.5em; }
        table { 
            font-size: 1em; /* 稍微减小字体大小 */
            display: table; /* 确保表格保持表格布局 */
            width: 100%;
        }
        thead { display: none; } /* 隐藏表头 */
        tr { 
            display: table-row; /* 保持行布局 */
            border-bottom: 1px solid var(--color-border); /* 只在行之间添加边框 */
            background: none; /* 移除背景色 */
            margin-bottom: 0; /* 移除行间距 */
            padding: 0; /* 移除内边距 */
        }
        td { 
            display: table-cell; /* 保持单元格布局 */
            padding: 0.4em 0.3em; /* 减小内边距 */
            border: none; /* 移除单元格边框 */
            position: static; /* 移除相对定位 */
            text-align: left; /* 左对齐文本 */
            font-size: 1em; /* 稍微减小字体大小 */
        }
        td:before { display: none; } /* 移除伪元素 */
        
        /* 特定列的样式调整 */
        td:nth-child(1) { /* 名称列 */
            padding-left: 0.5em; /* 增加左侧内边距 */
        }
        td:nth-child(3) { /* 大小列 */
            text-align: right; /* 右对齐 */
            width: 15%; /* 增加宽度 */
            padding-right: 0.5em; /* 增加右侧内边距 */
            white-space: nowrap; /* 防止换行 */
        }
        
        /* 文件名单元格特殊处理 */
        .filename-cell {
            padding-left: 0.5em !important;
            flex: none; /* 移除弹性布局 */
            order: 0; /* 恢复顺序 */
            margin-bottom: 0; /* 移除底部边距 */
        }
        
        /* 调整分页样式 */
        .pagination {
            margin-top: 1em;
            font-size: 0.9em;
        }
        
        /* 调整按钮样式 */
        .view-btn {
            padding: 0.4em 0.8em;
            font-size: 0.9em;
            margin: 0.3em 0.3em 0.3em 0;
        }
    }

    /* 图片查看器样式 */
    #image-viewer { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: var(--color-black); z-index: 1000; overflow: hidden; }
    #viewer-close { position: absolute; top: 20px; right: 35px; color: var(--color-white); font-size: 40px; font-weight: bold; cursor: pointer; z-index: 1001; }
    #viewer-scroll-container { height: calc(100vh - 10px); overflow-y: auto; position: relative; }
    #viewer-container { position: relative; }
    #viewer-phantom { position: absolute; top: 0; left: 0; width: 100%; pointer-events: none; }
    .img-wrap { position: absolute; width:  var(--thumbnail-size); height: var(--thumbnail-size); display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 5px; box-shadow: 0 2px 6px var(--color-shadow); cursor: pointer; transition: transform 0.2s; transform: translateZ(0); }
    .img-item { width: 100%; height: 100%; object-fit: cover; }
    .modal { 
        display: none; 
        position: fixed; 
        z-index: 1001; 
        left: 0; 
        top: 0; 
        width: 100%; 
        height: 100%; 
        background-color: var(--color-overlay); 
        /* 添加以下属性使内容居中 */
        justify-content: center;
        align-items: center;
    }
    .modal.show { 
        display: flex; /* 修改为flex以启用居中布局 */
    }
    .modal-content { 
        max-width: 100%; 
        max-height: 100%; 
        object-fit: contain;
        /* 添加以下属性确保图片在容器内居中 */
        margin: auto;
        display: block;
    }
    .close { 
        position: absolute; 
        top: 20px; 
        right: 35px; 
        color: var(--color-white); 
        font-size: 40px; 
        font-weight: bold; 
        cursor: pointer; 
        z-index: 1002; /* 提高z-index确保关闭按钮在图片上方 */
    }
    .close:hover { color: #ccc; }

    /* 媒体播放器样式 */
    .media-player-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: var(--color-overlay);
        z-index: 1000;
        display: none;
        justify-content: center;
        align-items: center;
    }
    .media-player-container.show {
        display: flex;
    }
    .media-player {
        display: flex;
        flex-direction: column;
        width: 100%;
        max-width: 100vw;
        max-height: 100vh;
        background: var(--color-black);
        border-radius: 8px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        overflow: hidden;
        margin: auto;
    }
    .media-player video, .media-player audio {
        width: 100%;
        height: 100%;
        max-height: 100vh;
        object-fit: contain;
        margin: 0 auto;
        outline: none;
    }
    /* 确保视频容器正确填充空间 */
    .media-player > video,
    .media-player > audio {
        flex: 1; /* 占据所有可用空间 */
        min-height: 0; /* 允许缩小 */
        object-fit: contain;
        width: 100%;
    }
    /* 确保视频元素在容器内垂直居中 */
    .media-player video {
        display: block;
        margin: auto;
    }
    /* 音频播放器样式 - 确保显示默认控制条 */
    .media-player audio {
        width: 100%;
        height: auto; /* 不指定固定高度，允许浏览器自适应 */
        min-height: 60px; /* 给音频播放器最小高度，保证进度条显示 */
        margin: 0 auto;
        outline: none;
        display: block; /* 确保显示 */
    }
    .media-controls {
        display: flex;
        flex-direction: column;
        padding: 10px;
        background: rgba(0, 0, 0, 0.7);
        min-height: 100px; /* 控制区域最小高度 */
    }
    /* 视频标题区域 - 固定2行高度，可滚动 */
    .media-title-container {
        height: 3em; /* 2行文字的高度 */
        overflow-y: auto; /* 垂直滚动 */
        margin-bottom: 10px;
        scrollbar-width: thin; /* Firefox */
    }

    .media-title-container::-webkit-scrollbar {
        width: 6px; /* WebKit浏览器滚动条宽度 */
    }

    .media-title-container::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 3px;
    }
    .media-title {
        color: var(--color-white);
        font-size: 16px;
        text-align: center;
        white-space: normal;
        word-break: break-word;
        overflow-wrap: break-word;
        line-height: 1.5;
        margin: 0;
        padding: 0;
    }
    .media-progress {
        width: 100%;
        height: 5px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
        cursor: pointer;
    }
    .media-progress-filled {
        height: 100%;
        background: var(--color-primary);
        border-radius: 2px;
        width: 0%;
    }
    .media-buttons {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 40px; /* 固定按钮高度 */;
    }
    /* 控制按钮容器 */
    .media-control-buttons {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        gap: 10px; /* 添加间距 */
    }
    /* 播放列表按钮样式 - 占据剩余空间 */
    .playlist-toggle-btn {
        background: var(--color-gray-600);
        color: var(--color-white);
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.2s;
        flex: 1; /* 占据剩余所有空间 */
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .playlist-toggle-btn:hover {
        background: var(--color-gray-900);
    }
    /* 连播复选框样式 - 固定宽度 */
    .continuous-play-label {
        display: flex;
        align-items: center;
        background: var(--color-gray-dark);
        color: var(--color-white);
        border: none;
        padding: 8px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.2s;
        white-space: nowrap;
        flex-shrink: 0; /* 防止缩小 */
    }
    .continuous-play-label:hover {
        background: var(--color-gray);
    }
    .continuous-play-label input[type="checkbox"] {
        margin-right: 5px;
        cursor: pointer;
    }
    /* 播放列表样式 - 作为弹出层 */
    .media-playlist {
        position: absolute;
        bottom: 100px; /* 在控制区域上方 */
        left: 50%;
        transform: translateX(-50%);
        max-width: 800px;
        width: 80%;
        max-height: 30vh;
        overflow-y: auto;
        background: var(--color-white);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10;
        padding: 10px;
        display: none;
    }
    .media-playlist.show {
        /* 当显示时 */
        display: block;
    }
    .media-playlist-item {
        padding: 10px;
        border-bottom: 1px solid var(--color-border);
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center; /* 垂直居中 */
    }
    .media-playlist-item:hover {
        background: var(--color-gray-light);
    }
    .media-playlist-item.active {
        background: var(--color-primary);
        color: var(--color-white);
    }
    .media-close-btn {
        position: absolute;
        top: 20px;
        right: 35px;
        color: var(--color-white);
        font-size: 40px;
        font-weight: bold;
        cursor: pointer;
        z-index: 1001;
    }

    /* 文本查看器样式 */
    .text-viewer-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: var(--color-white);
        z-index: 1000;
        display: none;
        flex-direction: column;
    }

    .text-viewer-container.show {
        display: flex;
    }

    .text-close-btn {
        position: absolute;
        top: 20px;
        right: 20px;
        color: var(--color-black);
        font-size: 40px;
        font-weight: bold;
        cursor: pointer;
        z-index: 1001;
    }

    .text-viewer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        padding-right: 60px; /* 为关闭按钮留出空间 */
        border-bottom: 1px solid var(--color-gray-200);
        background: var(--color-white);
        flex-shrink: 0;
        position: relative;
        z-index: 2;
    }

    .text-viewer-header h2 {
        margin: 0;
        color: var(--color-gray-900);
        font-size: 1.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 60%;
    }

    .text-viewer-options {
        display: flex;
        gap: 10px;
    }

    .text-viewer-btn {
        padding: 8px 16px;
        background: var(--color-gray-100);
        border: 1px solid var(--color-gray-300);
        border-radius: 4px;
        cursor: pointer;
        color: var(--color-gray-700);
        font-size: 14px;
        white-space: nowrap;
    }

    .text-viewer-btn:hover {
        background: var(--color-gray-200);
    }

    /* 关键修复：使用绝对定位而不是flex布局 */
    .text-viewer-content-container {
        position: absolute;
        top: 81px; /* 头部高度 */
        left: 0;
        right: 0;
        bottom: 0;
        overflow: hidden;
    }

    .text-viewer-content {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        overflow: auto;
        padding: 20px;
        -webkit-overflow-scrolling: touch;
        box-sizing: border-box;
        width: 100%;
        max-width: 800px;   /* 限制最大宽度 */
        margin: 0 auto;     /* 自动居中 */
    }
    @media (max-width: 600px) {
            .text-viewer-content {
            padding: 10px;
        }
    }

    .text-viewer-content pre {
        white-space: pre-wrap;     /* 允许换行 */
        word-break: break-all;     /* 强制断词，防止超长单词溢出 */
        margin: 0;
    }

    .text-viewer-content .hljs {
        padding: 0 !important;
    }

    /* 文本文件列表样式 */
    .text-playlist {
        position: absolute;
        top: 81px; /* 头部高度 */
        right: 20px;
        width: 300px;
        max-height: calc(100% - 101px); /* 头部高度 + 底部边距 */
        background: var(--color-white);
        border: 1px solid var(--color-gray-300);
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1002;
        overflow-y: auto;
        display: none;
    }

    .text-playlist.show {
        display: block;
    }

    .text-playlist-item {
        padding: 10px;
        border-bottom: 1px solid var(--color-gray-200);
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .text-playlist-item:hover {
        background: var(--color-gray-50);
    }

    .text-playlist-item.active {
        background: var(--color-primary-light);
        color: var(--color-primary);
    }

    /* 针对Edge的特殊修复 */
    @supports (-ms-ime-align:auto) {
        .text-viewer-content {
            overflow-y: scroll; /* 强制显示滚动条 */
            -ms-overflow-style: auto;
        }
    }

    /* 针对Chromium Edge的特殊修复 */
    @supports (selector(:focus-visible)) {
        .text-viewer-content {
            overflow: auto;
        }
    }

    .text-viewer-content pre {
        margin: 0;
        padding: 0;
        background: transparent !important;
    }

    .text-viewer-content code {
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
        font-size: 14px;
        line-height: 1.5;
        display: block;
        white-space: pre;
        overflow-x: auto;
    }

    /* 滚动条样式 - 确保在所有浏览器中一致 */
    .text-viewer-content::-webkit-scrollbar {
        width: 12px;
    }

    .text-viewer-content::-webkit-scrollbar-track {
        background: var(--color-gray-100);
        border-radius: 6px;
    }

    .text-viewer-content::-webkit-scrollbar-thumb {
        background: var(--color-gray-400);
        border-radius: 6px;
        border: 3px solid var(--color-white);
    }

    .text-viewer-content::-webkit-scrollbar-thumb:hover {
        background: var(--color-gray-500);
    }

    /* Firefox 滚动条样式 */
    .text-viewer-content {
        scrollbar-width: thin;
        scrollbar-color: var(--color-gray-400) var(--color-gray-100);
    }

    /* Edge滚动条样式 */
    .text-viewer-content {
        -ms-overflow-style: auto;
    }

    /* 确保代码高亮区域可以滚动 */
    .hljs {
        overflow: visible !important;
        display: block;
    }
</style>
<!-- 使用preload提高CSS加载性能 -->
<link rel="preload" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
"""

# 文件上传HTML
UPLOAD_FILE_HTML = """
<div class="upload-container">
    <button class="view-btn" onclick="openFileDialog()">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
    </svg>上传</button>
    <input type="file" id="fileInput" style="display:none" multiple>
    <div class="upload-progress" id="uploadProgress"></div>
    <div class="drag-overlay" id="dragOverlay">
        <div class="drag-message">拖放到此处上传</div>
    </div>
</div>
"""

# 图片查看器HTML
IMAGE_VIEWER_HTML = """
<div id="imageModal" class="modal">
    <span class="close" onclick="closeModal()">&times;</span>
    <img class="modal-content" id="expandedImg">
</div>
"""

# 媒体播放器HTML
MEDIA_PLAYER_HTML = """
<div id="mediaPlayer" class="media-player-container">
    <span class="media-close-btn" onclick="closeMediaPlayer()">&times;</span>
    <div class="media-player">
        <video id="videoPlayer" controls style="display: none;">
            Your browser does not support the video tag.
        </video>
        <audio id="audioPlayer" controls style="display: none;">
            Your browser does not support the audio element.
        </audio>
        <div class="media-controls">
            <div class="media-title-container">
                <div class="media-title" id="mediaTitle">Media Title</div>
            </div>
            <div class="media-control-buttons">
                <button id="playlistToggleBtn" class="playlist-toggle-btn">显示播放列表</button>
                <label class="continuous-play-label">
                    <input type="checkbox" id="continuousPlayCheckbox" checked>
                    连播
                </label>
            </div>
        </div>
    </div>
    <div class="media-playlist" id="mediaPlaylist"></div>
</div>
"""

# 文本查看器HTML和JavaScript
TEXT_VIEWER_HTML = """
<div id="textViewer" class="text-viewer-container">
    <span class="text-close-btn" onclick="closeTextViewer()">&times;</span>
    <div class="text-viewer-header">
        <h2 id="textTitle">文本查看器</h2>
        <div class="text-viewer-options">
            <button id="textListToggle" class="text-viewer-btn" onclick="toggleTextList()">显示列表</button>
            <button id="textWrapToggle" class="text-viewer-btn" onclick="toggleTextWrap()">换行</button>
            <!-- <button class="text-viewer-btn" onclick="copyTextContent()">复制</button> -->
        </div>
    </div>
    <div class="text-viewer-content-container">
        <div class="text-viewer-content">
            <pre><code id="textContent" class="hljs"></code></pre>
        </div>
    </div>
    <!-- 文本文件列表 -->
    <div class="text-playlist" id="textPlaylist"></div>
</div>

"""

JS_SCRIPTS = """
<script>
    // 文件上传相关
    let uploads = {};

    function openFileDialog() {
        document.getElementById('fileInput').click();
    }

    document.getElementById('fileInput').addEventListener('change', function(e) {
        uploadFiles(e.target.files);
    });

    function uploadFiles(files) {
        const progressContainer = document.getElementById("uploadProgress");
        progressContainer.style.display = "block";
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileId = Date.now() + '-' + i;
            
            // 添加上传项目到界面
            const progressItem = document.createElement('div');
            progressItem.className = 'progress-item';
            progressItem.id = 'progress-' + fileId;
            
            const fileName = document.createElement('div');
            fileName.className = 'progress-filename';
            fileName.textContent = file.name;
            
            const progressBarContainer = document.createElement('div');
            progressBarContainer.className = 'progress-bar-container';
            
            const progressBar = document.createElement('div');
            progressBar.className = 'progress-bar-fill';
            progressBar.style.width = '0%';
            
            progressBarContainer.appendChild(progressBar);
            progressItem.appendChild(fileName);
            progressItem.appendChild(progressBarContainer);
            progressContainer.appendChild(progressItem);
            
            // 开始上传
            uploadFile(file, fileId);
        }
    }

    function uploadFile(file, fileId) {
        uploads[fileId] = {
            file: file,
            loaded: 0,
            total: file.size
        };
        
        const formData = new FormData();
        formData.append("file", file);
        
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload?path=" + encodeURIComponent(window.location.pathname));
        
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const progress = (e.loaded / e.total) * 100;
                document.querySelector('#progress-' + fileId + ' .progress-bar-fill').style.width = progress + '%';
                uploads[fileId].loaded = e.loaded;
            }
        };
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                document.querySelector('#progress-' + fileId + ' .progress-bar-fill').style.background = 'var(--color-success)';
                setTimeout(() => {
                    document.getElementById('progress-' + fileId).remove();
                    if (document.getElementById('uploadProgress').children.length === 0) {
                        document.getElementById('uploadProgress').style.display = 'none';
                        location.reload();
                    }
                }, 1000);
            } else {
                document.querySelector('#progress-' + fileId + ' .progress-bar-fill').style.background = 'var(--color-error)';
                document.querySelector('#progress-' + fileId + ' .progress-filename').innerHTML += 
                    ' <span style="color:var(--color-error)">(上传失败)</span>';
            }
        };
        
        xhr.onerror = function() {
            document.querySelector('#progress-' + fileId + ' .progress-bar-fill').style.background = 'var(--color-error)';
            document.querySelector('#progress-' + fileId + ' .progress-filename').innerHTML += 
                ' <span style="color:var(--color-error)">(网络错误)</span>';
        };
        
        xhr.send(formData);
    }

    // 拖拽上传
    let dragCounter = 0;

    function showDragOverlay() {
        document.getElementById('dragOverlay').classList.add('active');
    }

    function hideDragOverlay() {
        document.getElementById('dragOverlay').classList.remove('active');
    }

    document.addEventListener('dragenter', function(e) {
        e.preventDefault();
        dragCounter++;
        showDragOverlay();
    });

    document.addEventListener('dragover', function(e) {
        e.preventDefault();
    });

    document.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            hideDragOverlay();
        }
    });

    document.addEventListener('drop', function(e) {
        e.preventDefault();
        dragCounter = 0;
        hideDragOverlay();
        
        if (e.dataTransfer.files.length > 0) {
            uploadFiles(e.dataTransfer.files);
        }
    });


    // 图像查看器相关
    // 获取CSS变量值
    function getCSSVariable(name) {
        const root = getComputedStyle(document.documentElement);
        const value = root.getPropertyValue(name).trim();
        return parseInt(value) || 0;
    }
    
    // 全局变量
    let viewerRenderedItems = new Map();
    let viewerCols = 0;
    const ITEM_WIDTH = getCSSVariable('--thumbnail-size');
    const ITEM_HEIGHT = getCSSVariable('--thumbnail-size');
    const GAP = getCSSVariable('--thumbnail-gap');
    const MOVE_THRESHOLD = getCSSVariable('--move-threshold');
    let rowHeight = ITEM_HEIGHT + GAP;
    let viewerFilesList = [];
    let debouncedHandleResize;
    let debouncedHandleViewerScroll;
    
    // 图片查看器导航变量
    let currentImageIndex = 0;
    let touchStartY = 0;
    let touchStartX = 0;
    
    function viewImages() {
        // 创建图片查看器容器
        const viewer = document.createElement('div');
        viewer.id = 'image-viewer';
        
        // 创建关闭按钮
        const closeBtn = document.createElement('span');
        closeBtn.id = 'viewer-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = closeImageViewer;
        
        // 创建滚动容器
        const scrollContainer = document.createElement('div');
        scrollContainer.id = 'viewer-scroll-container';
        
        // 创建图片容器
        const container = document.createElement('div');
        container.id = 'viewer-container';
        
        // 创建虚拟元素用于计算滚动
        const phantom = document.createElement('div');
        phantom.id = 'viewer-phantom';
        
        container.appendChild(phantom);
        scrollContainer.appendChild(container);
        viewer.appendChild(closeBtn);
        viewer.appendChild(scrollContainer);
        document.body.appendChild(viewer);
        document.body.style.overflow = 'hidden';
        
        // 初始化图片查看器
        initImageViewer(imageData);
        
        // 添加窗口调整大小事件监听
        debouncedHandleResize = debounce(handleResize, 100);
        window.addEventListener('resize', debouncedHandleResize);
        
        // 添加键盘事件监听
        document.addEventListener('keydown', handleImageViewerKeydown);
        
        // 添加触摸事件监听
        document.addEventListener('touchstart', handleTouchStart, { passive: false });
        document.addEventListener('touchmove', handleTouchMove, { passive: false });
    }
    
    function closeImageViewer() {
        const viewer = document.getElementById('image-viewer');
        if (viewer) {
            document.body.removeChild(viewer);
            document.body.style.overflow = 'auto';
            // 清理资源
            viewerRenderedItems.forEach(value => {
                if (value.wrap && value.wrap.parentNode) {
                    value.wrap.parentNode.removeChild(value.wrap);
                }
            });
            viewerRenderedItems.clear();
            
            // 移除事件监听器
            if (debouncedHandleResize) {
                window.removeEventListener('resize', debouncedHandleResize);
            }
            // 移除滚动事件监听器
            const scrollContainer = document.getElementById('viewer-scroll-container');
            if (debouncedHandleViewerScroll && scrollContainer) {
                scrollContainer.removeEventListener('scroll', debouncedHandleViewerScroll);
            }
            
            // 移除键盘和触摸事件监听
            document.removeEventListener('keydown', handleImageViewerKeydown);
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
        }
    }
    
    function initImageViewer(images) {
        viewerFilesList = images;
        calculateViewerLayout();
        updateViewerVisibleItems();
        
        // 添加滚动事件监听
        const scrollContainer = document.getElementById('viewer-scroll-container');
        debouncedHandleViewerScroll = debounce(handleViewerScroll, 50);
        scrollContainer.addEventListener('scroll', debouncedHandleViewerScroll);
        
        // 添加点击事件打开大图
        document.getElementById('viewer-container').addEventListener('click', function(e) {
            const img = e.target.closest('.img-item');
            if (img) {
                const index = parseInt(img.parentElement.getAttribute('data-index'));
                openModal(img.src, index);
            }
        });
    }
    
    function calculateViewerLayout() {
        const scrollContainer = document.getElementById('viewer-scroll-container');
        const containerWidth = scrollContainer.clientWidth;
        viewerCols = Math.max(1, Math.floor((containerWidth + GAP) / (ITEM_WIDTH + GAP)));

        const totalRows = Math.ceil(viewerFilesList.length / viewerCols);
        const totalHeight = totalRows * rowHeight - GAP;
        document.getElementById('viewer-phantom').style.height = `${totalHeight}px`;
    }

    function updateViewerVisibleItems() {
        const scrollContainer = document.getElementById('viewer-scroll-container');
        const scrollTop = scrollContainer.scrollTop;
        const clientHeight = scrollContainer.clientHeight;
        const buffer = 3;

        const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - buffer);
        const endRow = Math.ceil((scrollTop + clientHeight) / rowHeight) + buffer;
        const startIndex = Math.max(0, startRow * viewerCols);
        const endIndex = Math.min(viewerFilesList.length, endRow * viewerCols);

        // 移除不可见项
        viewerRenderedItems.forEach((value, index) => {
            if (index < startIndex || index >= endIndex) {
                if (value.wrap && value.wrap.parentNode) {
                    value.wrap.parentNode.removeChild(value.wrap);
                }
                viewerRenderedItems.delete(index);
            }
        });

        // 添加/更新可见项
        for (let i = startIndex; i < endIndex; i++) {
            if (i >= viewerFilesList.length) break;

            const col = i % viewerCols;
            const row = Math.floor(i / viewerCols);
            const left = col * (ITEM_WIDTH + GAP);
            const top = row * rowHeight;

            if (viewerRenderedItems.has(i)) {
                const item = viewerRenderedItems.get(i);
                item.wrap.style.left = `${left}px`;
                item.wrap.style.top = `${top}px`;
            } else {
                const image = viewerFilesList[i];
                const wrap = document.createElement('div');
                wrap.className = 'img-wrap';
                wrap.style.cssText = `left: ${left}px; top: ${top}px; width: ${ITEM_WIDTH}px; height: ${ITEM_HEIGHT}px;`;
                wrap.setAttribute('data-index', i);

                const img = document.createElement('img');
                img.className = 'img-item';
                img.src = image.url;
                img.alt = image.name;
                img.loading = 'lazy';

                wrap.appendChild(img);
                document.getElementById('viewer-container').appendChild(wrap);

                viewerRenderedItems.set(i, { wrap, img });
            }
        }
    }

    function handleViewerScroll() {
        updateViewerVisibleItems();
    }
    
    function handleResize() {
        calculateViewerLayout();
        updateViewerVisibleItems();
    }

    function openModal(src, index) {
        currentImageIndex = index;
        document.getElementById('imageModal').classList.add('show');
        document.getElementById('expandedImg').src = src;
        document.title = viewerFilesList[currentImageIndex].name;
        
        // 添加键盘和触摸事件监听
        document.addEventListener('keydown', handleModalKeydown);
        document.getElementById('imageModal').addEventListener('touchstart', handleModalTouchStart, { passive: false });
        document.getElementById('imageModal').addEventListener('touchmove', handleModalTouchMove, { passive: false });
    }

    function closeModal() {
        document.title = title;
        document.getElementById('imageModal').classList.remove('show');
        
        // 移除键盘和触摸事件监听
        document.removeEventListener('keydown', handleModalKeydown);
        document.getElementById('imageModal').removeEventListener('touchstart', handleModalTouchStart);
        document.getElementById('imageModal').removeEventListener('touchmove', handleModalTouchMove);
    }
    
    function showNextImage() {
        if (currentImageIndex < viewerFilesList.length - 1) {
            currentImageIndex++;
            document.getElementById('expandedImg').src = viewerFilesList[currentImageIndex].url;
            document.title = viewerFilesList[currentImageIndex].name;
        }
    }
    
    function showPrevImage() {
        if (currentImageIndex > 0) {
            currentImageIndex--;
            document.getElementById('expandedImg').src = viewerFilesList[currentImageIndex].url;
            document.title = viewerFilesList[currentImageIndex].name;
        }
    }
    
    function handleImageViewerKeydown(e) {
        if (e.key === 'Escape') {
            closeImageViewer();
        }
    }
    
    function handleModalKeydown(e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            showNextImage();
            e.preventDefault();
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
            showPrevImage();
            e.preventDefault();
        } else if (e.key === 'Escape') {
            closeModal();
        }
    }
    
    function handleTouchStart(e) {
        touchStartY = e.touches[0].clientY;
        touchStartX = e.touches[0].clientX;
    }
    
    function handleTouchMove(e) {
        if (!touchStartY) return;
        
        const touchY = e.touches[0].clientY;
        const touchX = e.touches[0].clientX;
        const diffY = touchY - touchStartY;
        const diffX = touchX - touchStartX;
        
        // 如果是水平滑动，阻止默认行为（防止页面滚动）
        if (Math.abs(diffX) > Math.abs(diffY)) {
            e.preventDefault();
        }
    }
    
    function handleModalTouchStart(e) {
        touchStartY = e.touches[0].clientY;
        touchStartX = e.touches[0].clientX;
    }
    
    function handleModalTouchMove(e) {
        if (!touchStartY) return;
        
        const touchY = e.touches[0].clientY;
        const touchX = e.touches[0].clientX;
        const diffY = touchY - touchStartY;
        const diffX = touchX - touchStartX;
        
        // 如果是垂直滑动，切换图片
        if (Math.abs(diffY) > Math.abs(diffX) && Math.abs(diffY) > MOVE_THRESHOLD) {
            e.preventDefault();
            if (diffY > 0) {
                // 向下滑动，显示上一张
                showPrevImage();
            } else {
                // 向上滑动，显示下一张
                showNextImage();
            }
            touchStartY = 0;
        }
    }
    
    // 防抖函数
    function debounce(func, delay = 100) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
    
    // 模态框背景点击关闭
    document.getElementById('imageModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });


    // 媒体播放器相关
    let currentMediaType = '';
    let currentMediaIndex = 0;
    let mediaList = [];
    let isPlaying = false;
    let isMuted = false;
    let isPlaylistVisible = false;
    // 添加自动播放下一首的变量
    let autoPlayNext = true;
    
    // 触摸事件变量
    let mediaTouchStartY = 0;
    let mediaTouchStartX = 0;

    function viewVideos() {
        openMediaPlayer('video', videoData);
    }
    function viewAudios() {
        openMediaPlayer('audio', audioData);
    }
    function openMediaPlayer(type, mediaData) {
        currentMediaType = type;
        mediaList = mediaData;
        currentMediaIndex = 0;
        const player = document.getElementById('mediaPlayer');
        player.classList.add('show');
        document.body.style.overflow = 'hidden';
        // 隐藏播放列表
        const playlist = document.getElementById('mediaPlaylist');
        playlist.classList.remove('show');
        const toggleBtn = document.getElementById('playlistToggleBtn');
        toggleBtn.textContent = '显示播放列表';
        isPlaylistVisible = false;
        // 设置播放器
        const videoPlayer = document.getElementById('videoPlayer');
        const audioPlayer = document.getElementById('audioPlayer');
        if (type === 'video') {
            videoPlayer.style.display = 'block';
            audioPlayer.style.display = 'none';
            loadMedia(videoPlayer, 0);
        } else {
            videoPlayer.style.display = 'none';
            audioPlayer.style.display = 'block';
            loadMedia(audioPlayer, 0);
        }
        setupMediaEvents();
        
        // 添加键盘和触摸事件监听
        document.addEventListener('keydown', handleMediaKeydown);
        player.addEventListener('touchstart', handleMediaTouchStart, { passive: false });
        player.addEventListener('touchmove', handleMediaTouchMove, { passive: false });
    }
    function closeMediaPlayer() {
        document.title = title;
        const player = document.getElementById('mediaPlayer');
        player.classList.remove('show');
        document.body.style.overflow = 'auto';
        const videoPlayer = document.getElementById('videoPlayer');
        const audioPlayer = document.getElementById('audioPlayer');
        videoPlayer.pause();
        audioPlayer.pause();
        // 移除结束事件监听
        videoPlayer.onended = null;
        audioPlayer.onended = null;
        videoPlayer.onloadedmetadata = null;
        videoPlayer.ontimeupdate = null;
        audioPlayer.onloadedmetadata = null;
        audioPlayer.ontimeupdate = null;
        
        // 移除键盘和触摸事件监听
        document.removeEventListener('keydown', handleMediaKeydown);
        player.removeEventListener('touchstart', handleMediaTouchStart);
        player.removeEventListener('touchmove', handleMediaTouchMove);
    }
    // 修改：切换播放列表
    function togglePlaylist() {
        const playlist = document.getElementById('mediaPlaylist');
        const toggleBtn = document.getElementById('playlistToggleBtn');
        if (isPlaylistVisible) {
            playlist.classList.remove('show');
            toggleBtn.textContent = '显示播放列表';
        } else {
            // 如果是第一次显示，先渲染
            if (playlist.children.length === 0) {
                renderPlaylist();
            }
            playlist.classList.add('show');
            toggleBtn.textContent = '隐藏播放列表';
        }
        isPlaylistVisible = !isPlaylistVisible;
    }
    // 在媒体播放器容器显示时，添加全局点击监听
    document.addEventListener('click', function(event) {
        const playlist = document.getElementById('mediaPlaylist');
        const toggleBtn = document.getElementById('playlistToggleBtn');
        const mediaPlayer = document.getElementById('mediaPlayer');
        
        // 只有当播放列表可见时才进行检查
        if (isPlaylistVisible && mediaPlayer.classList.contains('show')) {
            // 检查点击的目标是否在播放列表内部或在切换按钮上
            const isClickInsidePlaylist = playlist && playlist.contains(event.target);
            const isClickOnToggleBtn = toggleBtn && toggleBtn.contains(event.target);
            
            // 如果点击在播放列表外部且不在切换按钮上，则隐藏
            if (!isClickInsidePlaylist && !isClickOnToggleBtn) {
                togglePlaylist(); // 复用已有的切换函数
            }
        }
    });
    function renderPlaylist() {
        const playlist = document.getElementById('mediaPlaylist');
        playlist.innerHTML = '';
        mediaList.forEach((media, index) => {
            const item = document.createElement('div');
            item.className = 'media-playlist-item';
            if (index === currentMediaIndex) {
                item.classList.add('active');
            }
            // 创建名称元素
            const nameSpan = document.createElement('span');
            nameSpan.textContent = media.name;
            nameSpan.style.flex = '1';
            nameSpan.style.overflow = 'hidden';
            nameSpan.style.textOverflow = 'ellipsis';
            nameSpan.style.whiteSpace = 'nowrap';

            // 创建大小元素
            const sizeSpan = document.createElement('span');
            sizeSpan.textContent = formatSize(media.size);
            sizeSpan.style.marginLeft = '10px';
            sizeSpan.style.flexShrink = '0';
            sizeSpan.style.color = 'var(--color-gray-subtext)';
            sizeSpan.style.fontSize = '0.9em';

            item.appendChild(nameSpan);
            item.appendChild(sizeSpan);

            item.onclick = () => {
                loadMedia(
                    currentMediaType === 'video' 
                        ? document.getElementById('videoPlayer') 
                        : document.getElementById('audioPlayer'),
                    index
                );
                // 点击后自动隐藏播放列表
                togglePlaylist();
            };
            playlist.appendChild(item);
        });
    }
    function loadMedia(player, index) {
        currentMediaIndex = index;
        player.src = mediaList[index].url;
        player.load();
        document.getElementById('mediaTitle').textContent = mediaList[index].name;
        document.title = mediaList[index].name;
        renderPlaylist();
        
        // 设置结束事件监听，用于自动播放下一个
        player.onended = function() {
            if (autoPlayNext && currentMediaIndex < mediaList.length - 1) {
                playNextMedia();
            }
        };
        
        player.play().catch(e => {
            console.log('Autoplay prevented:', e);
        });
    }
    function setupMediaEvents() {
        const videoPlayer = document.getElementById('videoPlayer');
        const audioPlayer = document.getElementById('audioPlayer');
        const player = currentMediaType === 'video' ? videoPlayer : audioPlayer;
        document.getElementById('playlistToggleBtn').onclick = togglePlaylist;
        
        // 设置连播复选框事件
        const continuousPlayCheckbox = document.getElementById('continuousPlayCheckbox');
        continuousPlayCheckbox.checked = autoPlayNext;
        continuousPlayCheckbox.onchange = function() {
            autoPlayNext = this.checked;
        };
        
        // 确保为当前播放器设置结束事件
        player.onended = function() {
            if (autoPlayNext && currentMediaIndex < mediaList.length - 1) {
                playNextMedia();
            }
        };
    }
    
    function playNextMedia() {
        if (currentMediaIndex < mediaList.length - 1) {
            loadMedia(
                currentMediaType === 'video' 
                    ? document.getElementById('videoPlayer') 
                    : document.getElementById('audioPlayer'),
                currentMediaIndex + 1
            );
        }
    }
    
    function playPrevMedia() {
        if (currentMediaIndex > 0) {
            loadMedia(
                currentMediaType === 'video' 
                    ? document.getElementById('videoPlayer') 
                    : document.getElementById('audioPlayer'),
                currentMediaIndex - 1
            );
        }
    }
    
    function handleMediaKeydown(e) {
        if (e.key === 'ArrowDown') {
            playNextMedia();
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            playPrevMedia();
            e.preventDefault();
        } else if (e.key === 'Escape') {
            closeMediaPlayer();
        }
    }
    
    function handleMediaTouchStart(e) {
        mediaTouchStartY = e.touches[0].clientY;
        mediaTouchStartX = e.touches[0].clientX;
    }
    
    function handleMediaTouchMove(e) {
        if (isPlaylistVisible) return;
        if (!mediaTouchStartY) return;
        
        const touchY = e.touches[0].clientY;
        const touchX = e.touches[0].clientX;
        const diffY = touchY - mediaTouchStartY;
        const diffX = touchX - mediaTouchStartX;
        
        // 如果是垂直滑动，切换媒体
        if (Math.abs(diffY) > Math.abs(diffX) && Math.abs(diffY) > MOVE_THRESHOLD) {
            e.preventDefault();
            if (diffY > 0) {
                // 向下滑动，显示上一个
                playPrevMedia();
            } else {
                // 向上滑动，显示下一个
                playNextMedia();
            }
            mediaTouchStartY = 0;
        }
    }
    
    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const minutes = Math.floor(seconds / 60);
        seconds = Math.floor(seconds % 60);
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }


    // 文本查看器相关
    let currentTextIndex = 0;
    let textList = [];
    let isTextWrapEnabled = true;
    let isTextListVisible = false;

    function viewTexts() {
        openTextViewer(textData);
    }

    function openTextViewer(textData) {
        textList = textData;
        currentTextIndex = 0;
        const viewer = document.getElementById('textViewer');
        viewer.classList.add('show');
        document.body.style.overflow = 'hidden';

        // 加载第一个文本文件
        loadText(0);

        // 添加键盘事件监听
        document.addEventListener('keydown', handleTextKeydown);
        
        // 添加全局点击监听，用于关闭列表
        document.addEventListener('click', handleGlobalClick);
    }

    function closeTextViewer() {
        document.title = title;
        const viewer = document.getElementById('textViewer');
        viewer.classList.remove('show');
        document.body.style.overflow = 'auto';

        // 移除键盘事件监听
        document.removeEventListener('keydown', handleTextKeydown);
        document.removeEventListener('click', handleGlobalClick);
        
        // 隐藏列表
        hideTextList();
    }

    function loadText(index) {
        if (index < 0 || index >= textList.length) return;

        currentTextIndex = index;
        const textFile = textList[index];

        // 更新标题
        document.title = textFile.name;
        document.getElementById('textTitle').textContent = textFile.name;

        // 显示加载中
        document.getElementById('textContent').textContent = '加载中...';

        // 获取文本内容
        fetch(textFile.url)
            .then(response => {
                if (!response.ok) throw new Error('网络响应不正常');
                return response.text();
            })
            .then(text => {
                // 设置文本内容并高亮
                const codeElement = document.getElementById('textContent');
                codeElement.textContent = text;

                // 应用高亮
                hljs.highlightElement(codeElement);

                // 应用换行设置
                applyTextWrap();
            })
            .catch(error => {
                document.getElementById('textContent').textContent = '加载失败: ' + error.message;
            });
    }

    function showNextText() {
        if (currentTextIndex < textList.length - 1) {
            loadText(currentTextIndex + 1);
        }
    }

    function showPrevText() {
        if (currentTextIndex > 0) {
            loadText(currentTextIndex - 1);
        }
    }

    function toggleTextWrap() {
        isTextWrapEnabled = !isTextWrapEnabled;
        applyTextWrap();

        // 更新按钮文本
        // document.getElementById('textWrapToggle').textContent =
        //    isTextWrapEnabled ? '禁用换行' : '自动换行';
    }

    function toggleTextList() {
        const playlist = document.getElementById('textPlaylist');
        const toggleBtn = document.getElementById('textListToggle');
        
        if (isTextListVisible) {
            hideTextList();
            toggleBtn.textContent = '显示列表';
        } else {
            renderTextList();
            playlist.classList.add('show');
            toggleBtn.textContent = '隐藏列表';
        }
        
        isTextListVisible = !isTextListVisible;
    }
    
    function hideTextList() {
        const playlist = document.getElementById('textPlaylist');
        const toggleBtn = document.getElementById('textListToggle');
        
        playlist.classList.remove('show');
        toggleBtn.textContent = '显示列表';
        isTextListVisible = false;
    }

    function renderTextList() {
        const playlist = document.getElementById('textPlaylist');
        playlist.innerHTML = '';
        
        textList.forEach((textFile, index) => {
            const item = document.createElement('div');
            item.className = 'text-playlist-item';
            if (index === currentTextIndex) {
                item.classList.add('active');
            }
            
            // 创建名称元素
            const nameSpan = document.createElement('span');
            nameSpan.textContent = textFile.name;
            nameSpan.style.flex = '1';
            nameSpan.style.overflow = 'hidden';
            nameSpan.style.textOverflow = 'ellipsis';
            nameSpan.style.whiteSpace = 'nowrap';

            // 创建大小元素
            const sizeSpan = document.createElement('span');
            sizeSpan.textContent = formatSize(textFile.size);
            sizeSpan.style.marginLeft = '10px';
            sizeSpan.style.flexShrink = '0';
            sizeSpan.style.color = 'var(--color-gray-subtext)';
            sizeSpan.style.fontSize = '0.9em';

            item.appendChild(nameSpan);
            item.appendChild(sizeSpan);

            item.onclick = () => {
                loadText(index);
                // 点击后自动隐藏列表
                hideTextList();
            };
            playlist.appendChild(item);
        });
    }

    function applyTextWrap() {
        const codeElement = document.getElementById('textContent');
        if (isTextWrapEnabled) {
            codeElement.style.whiteSpace = 'pre-wrap';
            codeElement.style.wordBreak = 'break-word';
        } else {
            codeElement.style.whiteSpace = 'pre';
            codeElement.style.wordBreak = 'normal';
        }
    }

    function copyTextContent() {
        const textContent = document.getElementById('textContent').textContent;
        navigator.clipboard.writeText(textContent)
            .then(() => {
                alert('内容已复制到剪贴板');
            })
            .catch(err => {
                console.error('复制失败:', err);
            });
    }

    function handleTextKeydown(e) {
        if (e.key === 'ArrowRight') {
            showNextText();
            e.preventDefault();
        } else if (e.key === 'ArrowLeft') {
            showPrevText();
            e.preventDefault();
        } else if (e.key === 'Escape') {
            closeTextViewer();
        }
    }
    
    function handleGlobalClick(e) {
        const playlist = document.getElementById('textPlaylist');
        const toggleBtn = document.getElementById('textListToggle');
        
        // 只有当列表可见时才进行检查
        if (isTextListVisible) {
            // 检查点击的目标是否在列表内部或在切换按钮上
            const isClickInsidePlaylist = playlist && playlist.contains(e.target);
            const isClickOnToggleBtn = toggleBtn && toggleBtn.contains(e.target);
            
            // 如果点击在列表外部且不在切换按钮上，则隐藏列表
            if (!isClickInsidePlaylist && !isClickOnToggleBtn) {
                hideTextList();
            }
        }
    }

    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 添加Edge特定的滚动事件处理
    if (navigator.userAgent.includes('Edge')) {
        document.addEventListener('DOMContentLoaded', function() {
            const textContent = document.getElementById('textContent');
            if (textContent) {
                // 确保代码块可以滚动
                textContent.style.overflow = 'auto';
                textContent.style.maxHeight = 'none';
                
                // 添加触摸事件支持
                textContent.addEventListener('touchstart', function(e) {
                    this.startY = e.touches[0].clientY;
                }, { passive: true });
                
                textContent.addEventListener('touchmove', function(e) {
                    if (!this.startY) return;
                    
                    const touchY = e.touches[0].clientY;
                    const diffY = this.startY - touchY;
                    
                    if (Math.abs(diffY) > 10) {
                        this.scrollTop += diffY;
                        this.startY = touchY;
                        e.preventDefault();
                    }
                }, { passive: false });
            }
        });
    }
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
"""


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True  # 自动回收线程
    allow_reuse_address = True  # 允许重用端口


class ThreadedHTTPSServer(ThreadedHTTPServer):
    """支持HTTPS的线程化HTTP服务器"""

    def __init__(self, server_address, RequestHandlerClass, cert_file, key_file):
        super().__init__(server_address, RequestHandlerClass)
        self.cert_file = cert_file
        self.key_file = key_file
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        self.socket = self.context.wrap_socket(self.socket, server_side=True)


class LRUCache:
    """LRU缓存实现，支持超时和容量限制"""

    def __init__(self, capacity=1000, timeout=300):  # 默认超时时间改为300秒
        self.capacity = capacity
        self.timeout = timeout
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key):
        """获取缓存项，如果存在且未超时则返回，否则返回None"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, timestamp = self.cache[key]
            # 检查是否超时
            if time.time() - timestamp > self.timeout:
                del self.cache[key]
                self.misses += 1
                return None

            # 移动到最近使用位置
            self.cache.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key, value):
        """设置缓存项"""
        with self.lock:
            current_time = time.time()

            if key in self.cache:
                # 更新现有项
                self.cache[key] = (value, current_time)
                self.cache.move_to_end(key)
            else:
                # 检查容量，删除最久未使用的项
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)
                    self.evictions += 1

                self.cache[key] = (value, current_time)

    def invalidate(self, key):
        """使指定键的缓存项失效"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def stats(self):
        """获取缓存统计信息"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": hit_rate,
                "size": len(self.cache),
                "capacity": self.capacity,
                "timeout": self.timeout,
            }


class FileServerHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，支持文件浏览和图片查看功能"""

    # 添加一个类级别的日志记录器
    logger = logging.getLogger("FileServerHandler")

    # 使用类变量共享缓存实例
    cache = LRUCache(capacity=CACHE_CAPACITY, timeout=CACHE_TIMEOUT)
    password = None  # 初始密码为None

    def log_message(self, format, *args):
        # 将访问日志写入文件日志（INFO 级别）
        self.logger.info(
            "%s - - [%s] %s"
            % (self.client_address[0], self.log_date_time_string(), format % args)
        )

    def check_authentication(self):
        """检查HTTP基本认证"""
        if not self.password:
            return True  # 未设置密码，允许访问

        auth_header = self.headers.get("Authorization")
        if auth_header:
            # 解码认证信息
            auth_type, auth_string = auth_header.split(" ", 1)
            if auth_type.lower() == "basic":
                decoded = base64.b64decode(auth_string).decode("utf-8")
                username, password = decoded.split(":", 1)
                if password == self.password:
                    return True

        # 认证失败，要求提供凭据
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="File Server"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Authentication required</h1></body></html>")
        return False

    def list_directory(self, path):
        """列出目录内容并支持分页"""
        try:
            # 获取当前页码
            page = self._get_current_page()

            # 获取当前页的文件和总页数
            (
                items,
                current_page_images,
                current_page_videos,
                current_page_audios,
                current_page_texts,
                total_pages,
            ) = self._get_paginated_files(path, page)

            # 生成HTML响应
            html = self._generate_html_response(
                path,
                page,
                total_pages,
                items,
                current_page_images,
                current_page_videos,
                current_page_audios,
                current_page_texts,
            )

            # 发送响应
            self._send_html_response(html)
            return None

        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

    def _get_cached_dir_info(self, base_path):
        """获取缓存的目录信息，若目录已修改或过期则重新读取"""
        cached = self.cache.get(base_path)
        try:
            current_mtime = os.path.getmtime(base_path)
        except OSError:
            current_mtime = 0

        if cached:
            dirs, files, cached_mtime = cached
            if current_mtime <= cached_mtime:
                return dirs, files
            else:
                self.cache.invalidate(base_path)  # 失效缓存

        dirs, files = self._scan_directory(base_path)
        self.cache.set(base_path, (dirs, files, current_mtime))
        return dirs, files

    def _scan_directory(self, base_path):
        """扫描目录，返回目录和文件列表"""
        dirs = []
        files = []

        try:
            with os.scandir(base_path) as entries:
                for entry in entries:
                    # 跳过隐藏文件
                    if entry.name.startswith("."):
                        continue

                    try:
                        if entry.is_dir():
                            dirs.append((entry.name, entry.name))
                        else:
                            # 延迟获取文件大小，只在需要时获取
                            files.append((entry.name, entry.name, None))
                    except (OSError, FileNotFoundError):
                        # 跳过无法访问的文件或目录
                        continue
        except OSError:
            return [], []

        # 排序
        dirs.sort()
        files.sort()

        return dirs, files

    def _get_paginated_files(self, base_path, page):
        """获取当前页的文件列表，避免一次性处理所有文件"""
        # 获取缓存的目录和文件列表
        dirs, files = self._get_cached_dir_info(base_path)

        # 合并目录和文件列表
        all_items = dirs + files

        # 计算总页数
        total_items = len(all_items)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        # 获取当前页的项目
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_page_items = all_items[start_idx:end_idx]

        # 延迟获取文件大小和图片信息
        processed_items = []
        current_page_images = []
        current_page_videos = []
        current_page_audios = []
        current_page_texts = []

        for item in current_page_items:
            if len(item) == 2:  # 是目录
                processed_items.append(item)
            else:  # 是文件
                display_name, link_name, _ = item
                # 延迟获取文件大小
                try:
                    full_path = os.path.join(base_path, link_name)
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0

                processed_items.append((display_name, link_name, size))

                # 检查是否是图片、视频、音频、文本文件
                ext = os.path.splitext(display_name)[1].lower()
                encoded_name = quote(link_name)
                if ext in IMAGE_EXTENSIONS:
                    current_page_images.append(
                        {"name": display_name, "url": encoded_name}
                    )
                elif ext in VIDEO_EXTENSIONS:
                    current_page_videos.append(
                        {
                            "name": display_name,
                            "url": encoded_name,
                            "size": size,  # 新增：添加文件大小
                        }
                    )
                elif ext in AUDIO_EXTENSIONS:
                    current_page_audios.append(
                        {
                            "name": display_name,
                            "url": encoded_name,
                            "size": size,  # 新增：添加文件大小
                        }
                    )
                elif ext in TEXT_EXTENSIONS or (
                    not ext and display_name.lower() in COMMON_TEXT_FILES
                ):  # 新增：文本文件
                    current_page_texts.append(
                        {"name": display_name, "url": encoded_name, "size": size}
                    )

        return (
            processed_items,
            current_page_images,
            current_page_videos,
            current_page_audios,
            current_page_texts,
            total_pages,
        )

    def _get_current_page(self):
        """从查询参数获取当前页码"""
        query = urlparse(self.path).query
        params = parse_qs(query)
        page_str = params.get("page", ["1"])[0]

        # 确保页码是有效的数字
        try:
            # 移除任何非数字字符（如意外的斜杠）
            page_str = "".join(filter(str.isdigit, page_str))
            if not page_str:  # 如果过滤后为空字符串，使用默认值
                page_str = "1"
            return int(page_str)
        except (ValueError, TypeError):
            return 1  # 如果转换失败，返回第一页

    def _generate_html_response(
        self,
        path,
        page,
        total_pages,
        items,
        current_page_images,
        current_page_videos,
        current_page_audios,
        current_page_texts,
    ):
        """生成HTML响应内容"""
        decoded_path = unquote(self.path)
        title = f"{escape(decoded_path)}"

        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{title}</title>",
            f"{CSS_STYLES}",
            """<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAyNCIgaGVpZ2h0PSIxMDI0IiB2aWV3Qm94PSIwIDAgMTAyNCAxMDI0IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik05NzAuNjY2NjY3IDIxMy4zMzMzMzNINTQ2LjU4NjY2N2ExMC41NzMzMzMgMTAuNTczMzMzIDAgMCAxLTcuNTQtMy4xMjY2NjZMNDE5Ljc5MzMzMyAxMDAuOTUzMzMzQTUyLjk4NjY2NyA1Mi45ODY2NjcgMCAwIDAgMzkyLjA4IDg1LjMzMzMzM0g5NmE1My4zOTMzMzMgNTMuMzkzMzMzIDAgMCAwLTUzLjMzMzMzMyA1My4zMzMzMzR2NzA0YTUzLjM5MzMzMyA1My4zOTMzMzMgMCAwIDAgNTMuMzMzMzMzIDUzLjMzMzMzM2g4NzQuNjY2NjY3YTUzLjM5MzMzMyA1My4zOTMzMzMgMCAwIDAgNTMuMzMzMzMzLTUzLjMzMzMzM1YyNjYuNjY2NjY3YTUzLjM5MzMzMyA1My4zOTMzMzMgMCAwIDAtNTMuMzMzMzMzLTUzLjMzMzMzNHogbTEwLjY2NjY2NiA2MjkuMzMzMzM0YTEwLjY2NjY2NyAxMC42NjY2NjcgMCAwIDEtMTAuNjY2NjY2IDEwLjY2NjY2Nkg5NmExMC42NjY2NjcgMTAuNjY2NjY3IDAgMCAxLTEwLjY2NjY2Ny0xMC42NjY2NjZWMTM4LjY2NjY2N2ExMC42NjY2NjcgMTAuNjY2NjY3IDAgMCAxIDEwLjY2NjY2Ny0xMC42NjY2NjdoMjk2LjA4YTEwLjU3MzMzMyAxMC41NzMzMzMgMCAwIDEgNy41NCAzLjEyNjY2N2wxMDkuMjUzMzMzIDEwOS4yNTMzMzNBNTIuOTg2NjY3IDUyLjk4NjY2NyAwIDAgMCA1NDYuNTg2NjY3IDI1Nkg5NzAuNjY2NjY3YTEwLjY2NjY2NyAxMC42NjY2NjcgMCAwIDEgMTAuNjY2NjY2IDEwLjY2NjY2N3pNNjQwIDM0MS4zMzMzMzNhODUuMzMzMzMzIDg1LjMzMzMzMyAwIDAgMC04MS44MjY2NjcgMTA5LjU1MzMzNGwtNzEuNjczMzMzIDQzYTg1LjMzMzMzMyA4NS4zMzMzMzMgMCAxIDAtNi41NjY2NjcgMTI3LjM5MzMzM2wzOC41MDY2NjcgMjguODhhODUuNTI2NjY3IDg1LjUyNjY2NyAwIDEgMCAyNS42MjY2NjctMzQuMTA2NjY3bC0zOC41MDY2NjctMjguODhhODUuMzMzMzMzIDg1LjMzMzMzMyAwIDAgMCAyLjkzMzMzMy01Ni43MjY2NjZsNzEuNjczMzM0LTQzQTg1LjMzMzMzMyA4NS4zMzMzMzMgMCAxIDAgNjQwIDM0MS4zMzMzMzN6TTQyNi42NjY2NjcgNTk3LjMzMzMzM2E0Mi42NjY2NjcgNDIuNjY2NjY3IDAgMSAxIDQyLjY2NjY2Ni00Mi42NjY2NjYgNDIuNzEzMzMzIDQyLjcxMzMzMyAwIDAgMS00Mi42NjY2NjYgNDIuNjY2NjY2eiBtMTcwLjY2NjY2NiA0Mi42NjY2NjdhNDIuNjY2NjY3IDQyLjY2NjY2NyAwIDEgMS00Mi42NjY2NjYgNDIuNjY2NjY3IDQyLjcxMzMzMyA0Mi43MTMzMzMgMCAwIDEgNDIuNjY2NjY2LTQyLjY2NjY2N3ogbTQyLjY2NjY2Ny0xNzAuNjY2NjY3YTQyLjY2NjY2NyA0Mi42NjY2NjcgMCAxIDEgNDIuNjY2NjY3LTQyLjY2NjY2NiA0Mi43MTMzMzMgNDIuNzEzMzMzIDAgMCAxLTQyLjY2NjY2NyA0Mi42NjY2NjZ6IiBmaWxsPSIjNUM1QzY2IiAvPjwvc3ZnPg=="/>""",
            "</head>",
            "<body>",
            '<div class="container">',
            '<div class="header">',
            "<h1>share 文件夹</h1>",
        ]

        html_parts.append('<div class="view-options">')
        html_parts.append(self._upload_file())
        # 如果有图片、视频、音频或文本，添加相应的按钮
        if current_page_images:
            html_parts.append(
                f"<script>var imageData = {json.dumps(current_page_images)};</script>"
            )
            html_parts.append('<button class="view-btn" onclick="viewImages()">')
            html_parts.append(
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
            )
            html_parts.append(
                '<path d="M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-4.86 8.86l-3 3.87L9 13.14 6 17h12l-3.86-5.14z"/>'
            )
            html_parts.append("</svg>")
            html_parts.append("图片")
            html_parts.append("</button>")

        if current_page_videos:
            html_parts.append(
                f"<script>var videoData = {json.dumps(current_page_videos)};</script>"
            )
            html_parts.append('<button class="view-btn" onclick="viewVideos()">')
            html_parts.append(
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
            )
            html_parts.append(
                '<path d="M15 8v8H5V8h10m1-2H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4V7c0-.55-.45-1-1-1z"/>'
            )
            html_parts.append("</svg>")
            html_parts.append("视频")
            html_parts.append("</button>")

        if current_page_audios:
            html_parts.append(
                f"<script>var audioData = {json.dumps(current_page_audios)};</script>"
            )
            html_parts.append('<button class="view-btn" onclick="viewAudios()">')
            html_parts.append(
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
            )
            html_parts.append(
                '<path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>'
            )
            html_parts.append("</svg>")
            html_parts.append("音频")
            html_parts.append("</button>")

        if current_page_texts:
            html_parts.append(
                f"<script>var textData = {json.dumps(current_page_texts)};</script>"
            )
            html_parts.append('<button class="view-btn" onclick="viewTexts()">')
            html_parts.append(
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
            )
            html_parts.append(
                '<path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>'
            )
            html_parts.append("</svg>")
            html_parts.append("代码")
            html_parts.append("</button>")

        html_parts.append("</div>")
        html_parts.append("</div>")  # 关闭header

        html_parts.extend(self._generate_pagination_buttons(page, total_pages))

        html_parts.extend(
            ["<table>", "<thead><tr><th>名称</th><th>大小</th></tr></thead>", "<tbody>"]
        )

        # 添加上级目录
        if self.path != "/":
            html_parts.append(
                '<tr><td colspan="3" class="filename-cell"><a href="../"> ..</a></td></tr>'
            )

        # 添加文件和目录列表
        html_parts.extend(self._generate_file_list(items))

        html_parts.extend(["</tbody></table>"])

        # 添加分页导航
        html_parts.extend(self._generate_pagination_buttons(page, total_pages))

        # 添加缓存统计信息（调试用）
        if os.environ.get("DEBUG_CACHE"):
            stats = self.cache.stats()
            html_parts.append(
                '<div style="margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px;">'
            )
            html_parts.append("<h3>缓存统计</h3>")
            html_parts.append(
                f"<p>命中率: {stats['hit_rate'] * 100:.1f}% ({stats['hits']}/{stats['hits'] + stats['misses']})</p>"
            )
            html_parts.append(f"<p>缓存大小: {stats['size']}/{stats['capacity']}</p>")
            html_parts.append(f"<p>超时时间: {stats['timeout']}秒</p>")
            html_parts.append(f"<p>驱逐次数: {stats['evictions']}</p>")
            html_parts.append("</div>")

        # 添加图片查看器、媒体播放器和文本查看器的HTML和JavaScript
        html_parts.append(self._generate_common_js())  # 公共JS
        html_parts.append(self._generate_image_viewer_html())
        html_parts.append(self._generate_media_player_html())
        html_parts.append(self._generate_text_viewer_html())

        html_parts.append("</div>")  # 关闭container
        html_parts.append(self._generate_js_scripts())  # JavaScript脚本
        html_parts.append("</body></html>")

        return "".join(html_parts)

    def _generate_common_js(self):
        """生成公共的JavaScript代码"""
        return """
        <script>
        // 公共JavaScript代码
        const title = document.title;
        </script>
        """

    def _generate_pagination_buttons(self, page, total_pages):
        """生成分页按钮，页数过多时简化显示"""
        buttons = ['<div class="pagination">']

        # 获取当前路径并确保格式正确
        current_path = self._get_current_path()

        # 上一页按钮
        if page > 1:
            buttons.append(
                f'<a href="{current_path}?page={page - 1}">&laquo; 上一页</a>'
            )

        # 确定要显示的页码范围
        max_visible_pages = 7  # 最多显示的页码数
        half_visible = max_visible_pages // 2

        start_page = max(1, page - half_visible)
        end_page = min(total_pages, start_page + max_visible_pages - 1)

        # 调整起始页码，确保显示足够多的页码
        if end_page - start_page + 1 < max_visible_pages:
            start_page = max(1, end_page - max_visible_pages + 1)

        # 显示第一页和省略号（如果需要）
        if start_page > 1:
            buttons.append(f'<a href="{current_path}?page=1">1</a>')
            if start_page > 2:
                buttons.append('<span class="ellipsis">...</span>')

        # 显示页码
        for i in range(start_page, end_page + 1):
            if i == page:
                buttons.append(f"<strong>{i}</strong>")
            else:
                buttons.append(f'<a href="{current_path}?page={i}">{i}</a>')

        # 显示省略号和最后一页（如果需要）
        if end_page < total_pages:
            if end_page < total_pages - 1:
                buttons.append('<span class="ellipsis">...</span>')
            buttons.append(
                f'<a href="{current_path}?page={total_pages}">{total_pages}</a>'
            )

        # 下一页按钮
        if page < total_pages:
            buttons.append(
                f'<a href="{current_path}?page={page + 1}">下一页 &raquo;</a>'
            )

        buttons.append("</div>")
        return buttons

    def _get_current_path(self):
        """获取当前路径并确保格式正确"""
        parsed = urlparse(self.path)
        path = parsed.path

        # 确保路径以斜杠结尾（如果是目录）
        if not path.endswith("/"):
            # 检查这是否是一个目录请求
            if not os.path.basename(path) or "." not in os.path.basename(path):
                path += "/"

        return path

    def _generate_file_list(self, items):
        """生成文件列表HTML"""
        file_list_html = []
        for item in items:
            if len(item) == 2:  # 是目录
                display_name, link_name = item
                link = quote(link_name) + "/"
                file_list_html.append(
                    f"<tr>"
                    f'<td class="filename-cell" data-label="名称" title="{escape(display_name)}"><a href="{link}"> {escape(display_name)}</a></td>'
                    # f'<td data-label="类型">目录</td>'
                    f'<td data-label="大小">-</td>'
                    f"</tr>"
                )
            else:
                display_name, link_name, size = item
                link = quote(link_name)
                size_str = self._format_size(size)
                file_list_html.append(
                    f"<tr>"
                    f'<td class="filename-cell" data-label="名称" title="{escape(display_name)}"><a href="{link}"> {escape(display_name)}</a></td>'
                    # f'<td data-label="类型">文件</td>'
                    f'<td data-label="大小">{size_str}</td>'
                    f"</tr>"
                )
        return file_list_html

    def _upload_file(self):
        """生成上传文件按钮和相关HTML"""
        return UPLOAD_FILE_HTML

    def _generate_image_viewer_html(self):
        """生成图片查看器HTML和JavaScript"""
        return IMAGE_VIEWER_HTML

    def _generate_media_player_html(self):
        """生成媒体播放器HTML和JavaScript"""
        return MEDIA_PLAYER_HTML

    def _generate_text_viewer_html(self):
        """生成文本查看器HTML和JavaScript"""
        return TEXT_VIEWER_HTML

    def _generate_js_scripts(self):
        """生成JavaScript脚本"""
        return JS_SCRIPTS

    def _send_html_response(self, html_content):
        """发送HTML响应"""
        encoded = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _format_size(self, size):
        """将字节转换为可读格式"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def do_GET(self):
        """处理GET请求，检查认证，文本文件动态检测编码，添加缓存统计端点，支持视频音频文件的Range请求"""

        # 检查认证
        if not self.check_authentication():
            return

        path = self.translate_path(self.path)
        _, ext = os.path.splitext(path)

        # 处理文本文件
        if os.path.isfile(path) and ext.lower() in TEXT_EXTENSIONS:
            try:
                # 首先以二进制模式读取文件内容
                with open(path, "rb") as f:
                    raw_content = f.read()

                # 尝试一系列常见编码
                encodings_to_try = [
                    "utf-8",  # 最通用的编码
                    "gbk",  # 中文Windows常用
                    "big5",  # 繁体中文
                    "shift_jis",  # 日文
                    "euc-kr",  # 韩文
                    "iso-8859-1",  # 西欧语言
                    "cp1252",  # Windows西欧语言
                    "utf-16",  # Unicode
                    "utf-16le",  # Unicode小端序
                    "utf-16be",  # Unicode大端序
                ]

                content = None

                for encoding in encodings_to_try:
                    try:
                        content = raw_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                # 如果所有编码都失败，使用替换错误处理
                if content is None:
                    content = raw_content.decode("utf-8", errors="replace")

                # 将内容编码为UTF-8发送
                content = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
                return

        # 处理视频文件的Range请求
        if (
            os.path.isfile(path)
            and ext.lower() in VIDEO_EXTENSIONS
            or ext.lower() in AUDIO_EXTENSIONS
        ):
            self._handle_video_request(path)
            return

        # 处理缓存统计端点
        if self.path == "/cache-stats":
            # 返回缓存统计信息
            stats = self.cache.stats()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        if self.path == "/cache-clear":
            # 清空缓存
            self.cache.clear()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Cache cleared")
            return

        if self.path == "/cache-config":
            # 配置缓存参数
            query = urlparse(self.path).query
            params = parse_qs(query)

            if "timeout" in params:
                try:
                    new_timeout = int(params["timeout"][0])
                    if new_timeout > 0:
                        self.cache.timeout = new_timeout
                except ValueError:
                    pass

            if "capacity" in params:
                try:
                    new_capacity = int(params["capacity"][0])
                    if new_capacity > 0:
                        self.cache.capacity = new_capacity
                except ValueError:
                    pass

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.cache.stats()).encode("utf-8"))
            return

        # 正常处理其他请求
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            # 客户端提前关闭连接
            self.logger.warning(f"客户端 {self.client_address} 提前关闭了连接.")
            return
        except Exception as e:
            # 其他异常，记录日志但不中断服务器
            self.logger.error(f"处理请求时发生异常: {e}")
            try:
                self.send_error(500, f"Server error: {str(e)}")
            except (BrokenPipeError, ConnectionResetError):
                # 即使在发送错误响应时客户端也断开了连接
                self.logger.warning(
                    f"客户端 {self.client_address} 在发送错误响应时提前关闭了连接."
                )
                return

    def _handle_video_request(self, path):
        """处理视频文件的Range请求，支持分段加载（安全且高效）"""
        try:
            file_size = os.path.getsize(path)
            range_header = self.headers.get("Range")
            chunk_size = 1024 * 1024  # 1MB 分块

            if not range_header:
                # 发送整个文件
                self.send_response(200)
                self.send_header("Content-type", self.guess_type(path))
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                try:
                    with open(path, "rb") as f:
                        # 关键：使用分块读取 + flush，确保 HTTPS 下可靠
                        while chunk := f.read(chunk_size):
                            self.wfile.write(chunk)
                            self.wfile.flush()  # 强制刷新 SSL 缓冲区
                except (BrokenPipeError, ConnectionResetError):
                    self.logger.warning(f"客户端 {self.client_address} 提前关闭了连接.")
                    return
                return

            # 解析 Range 头
            byte_range = self._parse_range_header(range_header, file_size)
            if not byte_range:
                self.send_error(416, "Requested Range Not Satisfiable")
                return

            start, end = byte_range
            content_length = end - start + 1

            # 发送 206 Partial Content
            self.send_response(206)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            # 安全发送文件：分块读取 + flush
            try:
                with open(path, "rb") as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        read_size = min(chunk_size, remaining)
                        data = f.read(read_size)
                        if not data:
                            break
                        self.wfile.write(data)
                        self.wfile.flush()  # 🔥 关键修复
                        remaining -= len(data)
            except (BrokenPipeError, ConnectionResetError):
                self.logger.warning(f"客户端 {self.client_address} 提前关闭了连接.")
                return
            except Exception as e:
                self.logger.error(f"发送文件时出错: {e}")
                return

        except Exception as e:
            self.logger.error(f"处理视频请求时出错: {e}")
            self.send_error(500, f"Video request failed: {e}")

    def _parse_range_header(self, range_header, file_size):
        """解析Range请求头，返回(start, end)元组"""
        if not range_header.startswith("bytes="):
            return None

        ranges = range_header[6:].split(",")
        if len(ranges) != 1:
            # 只支持单个范围请求
            return None

        range_str = ranges[0].strip()
        if "-" not in range_str:
            return None

        start_str, end_str = range_str.split("-", 1)

        try:
            if not start_str and end_str:
                # 格式: -500 (最后500字节)
                end = int(end_str)
                if end > file_size:
                    end = file_size
                start = file_size - end
                end = file_size - 1
            elif start_str and not end_str:
                # 格式: 500- (从500字节到文件末尾)
                start = int(start_str)
                if start >= file_size:
                    return None
                end = file_size - 1
            else:
                # 格式: 500-1000
                start = int(start_str)
                end = int(end_str)
                if start >= file_size or end >= file_size or start > end:
                    return None

            return (start, end)
        except ValueError:
            return None

    def do_POST(self):
        """处理POST请求，主要是文件上传"""
        # 检查认证
        if not self.check_authentication():
            return

        parsed_path = urlparse(self.path)
        if parsed_path.path == "/upload":
            self.handle_file_upload(parsed_path)
        else:
            self.send_error(404, "Unknown POST endpoint")

    def handle_file_upload(self, parsed_path):
        """接收并保存上传的文件到当前浏览目录"""
        try:
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self.send_error(400, "Invalid Content-Type")
                return

            boundary = content_type.split("boundary=")[-1].encode()
            remain_bytes = int(self.headers["Content-Length"])

            # boundary
            line = self.rfile.readline()
            remain_bytes -= len(line)
            if boundary not in line:
                self.send_error(400, "Content does not start with boundary")
                return

            # Content-Disposition
            line = self.rfile.readline()
            remain_bytes -= len(line)
            disposition = line.decode()
            if "filename=" not in disposition:
                self.send_error(400, "No filename found")
                return
            filename = disposition.split("filename=")[1].strip().strip('"')

            # 安全处理文件名，防止路径遍历攻击
            filename = os.path.basename(filename)
            if not filename:
                self.send_error(400, "Invalid filename")
                return

            # 跳过 Content-Type 和空行
            line = self.rfile.readline()
            remain_bytes -= len(line)  # 修正：使用新读取的line
            line = self.rfile.readline()
            remain_bytes -= len(line)  # 修正：使用新读取的line

            # ⚡ 关键修正：把 URL 路径转为文件系统路径
            query = parse_qs(parsed_path.query)
            url_path = unquote(query.get("path", [""])[0])  # 例如 "Downloads/"
            rel_path = url_path.lstrip("/")  # 变成 "Downloads"
            target_dir = (
                os.path.join(self.directory, rel_path) if rel_path else self.directory
            )

            # 安全检查：确保目标目录在服务器目录内
            target_dir = os.path.abspath(target_dir)
            server_root = os.path.abspath(self.directory)
            if not target_dir.startswith(server_root):
                self.send_error(403, "Access denied")
                return

            # 检查目标目录是否存在，不存在则创建
            if not os.path.exists(target_dir):
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except OSError as e:
                    self.send_error(500, f"Failed to create directory: {str(e)}")
                    return

            # 检查写入权限
            if not os.access(target_dir, os.W_OK):
                self.send_error(403, "No write permission for this directory")
                return

            save_path = os.path.join(target_dir, filename)

            # 处理文件名冲突
            if os.path.exists(save_path):
                # 分离文件名和扩展名
                name, ext = os.path.splitext(filename)
                counter = 1
                # 查找可用的文件名
                while os.path.exists(save_path):
                    filename = f"{name}_{counter}{ext}"
                    save_path = os.path.join(target_dir, filename)
                    counter += 1

            # 保存文件
            try:
                with open(save_path, "wb") as f:
                    prev_line = self.rfile.readline()
                    remain_bytes -= len(prev_line)
                    while remain_bytes > 0:
                        line = self.rfile.readline()
                        remain_bytes -= len(line)
                        if boundary in line:
                            # 移除行尾的CRLF或LF
                            if prev_line.endswith(b"\r\n"):
                                f.write(prev_line[:-2])
                            elif prev_line.endswith(b"\n"):
                                f.write(prev_line[:-1])
                            else:
                                f.write(prev_line)
                            break
                        else:
                            f.write(prev_line)
                            prev_line = line
                    # 确保文件完整写入
                    f.flush()
            except OSError as e:
                self.logger.error(f"保存文件时出错: {e}")
                self.send_error(500, f"Failed to save file: {str(e)}")
                return
            except Exception as e:
                self.logger.error(f"Unexpected error during file save: {e}")
                self.send_error(500, f"Unexpected error during file save: {str(e)}")
                return

            # 返回响应
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "success", "filename": filename}).encode()
            )

            # 使目录缓存失效，确保新文件立即显示
            self.cache.invalidate(target_dir)

        except UnicodeDecodeError:
            self.logger.error(f"请求头中存在无效编码")
            self.send_error(400, "Invalid encoding in request headers")
            return
        except KeyError:
            self.logger.error(f"请求中缺少必要参数")
            self.send_error(400, "Missing required parameter")
            return
        except Exception as e:
            self.logger.error(f"处理请求时发生异常: {e}")
            self.send_error(500, f"Unexpected error: {str(e)}")
            return


def get_log_directory():
    """根据系统平台获取推荐的日志目录"""
    system = platform.system().lower()

    if system == "windows":
        # Windows: 使用 %APPDATA% 目录
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        log_dir = os.path.join(base_dir, "Share", "Logs")
    elif system == "darwin":  # macOS
        # macOS: 使用 ~/Library/Logs 目录
        log_dir = os.path.expanduser("~/Library/Logs/Share")
    else:  # Linux 和其他 Unix 系统
        # 首先尝试用户目录
        base_dir = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        log_dir = os.path.join(base_dir, "share", "logs")

        # 如果用户目录不可写，尝试当前工作目录
        try:
            os.makedirs(log_dir, exist_ok=True)
            # 测试是否可写
            test_file = os.path.join(log_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except (PermissionError, OSError):
            # 回退到当前工作目录下的 logs 文件夹
            log_dir = os.path.join(os.getcwd(), "logs")

    # 创建日志目录
    try:
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except PermissionError:
        # 如果所有目录都不可写，使用临时目录
        import tempfile

        log_dir = os.path.join(tempfile.gettempdir(), "share_logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir


def setup_logging():
    try:
        log_dir = get_log_directory()
        log_file = os.path.join(log_dir, LOG_FILE_NAME)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        return log_file

    except Exception as e:
        print(f"无法设置文件日志: {e}，将使用控制台输出", file=sys.stderr)

        # 清理并回退到控制台
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return "console_only"


def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 创建一个临时socket连接来获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except (socket.error, OSError):
        return "127.0.0.1"


def validate_directory(path):
    """验证目录是否存在且可访问"""
    if not os.path.exists(path):
        raise ValueError(f"文件夹 '{path}' 不存在")
    if not os.path.isdir(path):
        raise ValueError(f"'{path}' 不是一个文件夹")
    if not os.access(path, os.R_OK):
        raise ValueError(f"没有读取文件夹 '{path}' 的权限")
    return path


def ensure_ssl_cert():
    """确保 SSL 证书存在，不存在则生成自签名证书"""
    os.makedirs(SSL_DIR, exist_ok=True)

    cert = CERT_FILE
    key = KEY_FILE

    if os.path.exists(cert) and os.path.exists(key):
        print(f"使用现有证书: {cert}")
        return cert, key

    print("正在生成自签名 HTTPS 证书...")

    # 检查 openssl 是否可用
    try:
        subprocess.run(
            ["openssl", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        print("错误：未找到 openssl 命令。")
        print("请安装 OpenSSL：")
        system = platform.system().lower()
        if system == "windows":
            print("  - 推荐安装 Git for Windows（自带 openssl）")
            print("  - 或安装 Cygwin / WSL")
        elif system == "darwin":
            print("  - 使用 Homebrew: brew install openssl")
        else:  # Linux
            print("  - Ubuntu/Debian: sudo apt install openssl")
            print("  - CentOS/RHEL: sudo yum install openssl")
        sys.exit(1)

    # 生成私钥和证书
    try:
        # 注意：Windows 上 shell=True 可能更兼容
        cmd = [
            "openssl",
            "req",
            "-x509",
            "-nodes",
            "-days",
            "365",
            "-newkey",
            "rsa:2048",
            "-keyout",
            key,
            "-out",
            cert,
            "-subj",
            "/C=CN/O=Local Share/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ]
        # Windows 不支持 -addext？尝试不加
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("警告：忽略 -addext 参数（可能系统不支持）")
            cmd.remove("-addext")
            cmd.remove("subjectAltName=DNS:localhost,IP:127.0.0.1")
            subprocess.run(cmd, check=True)

        # 设置权限（类 Unix）
        if hasattr(os, "chmod"):
            os.chmod(key, 0o600)
            os.chmod(cert, 0o644)

        print(f"证书已生成: {cert}")
        print(f"私钥已生成: {key}")
        print("⚠️ 浏览器将显示安全警告（自签名证书），请手动信任。")

    except subprocess.CalledProcessError as e:
        print(f"生成证书失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}")
        sys.exit(1)

    return cert, key


def serve_folder(
    folder, port=8000, host="0.0.0.0", password=None, cert_file=None, key_file=None
):
    """启动HTTP服务器提供文件夹服务"""
    try:
        # 设置密码
        FileServerHandler.password = password

        # 验证文件夹
        folder = validate_directory(folder)

        # 切换到指定文件夹作为服务器根目录
        os.chdir(folder)

        # 选择协议http或https
        if cert_file and key_file:
            scheme = "https"
            server = ThreadedHTTPSServer(
                (host, port), FileServerHandler, cert_file, key_file
            )
        else:
            scheme = "http"
            server = ThreadedHTTPServer((host, port), FileServerHandler)

        # 在服务器 socket 上设置 TCP 优化选项
        sock = server.socket
        sock.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
        )  # 禁用Nagle算法，减少小包延迟
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_SNDBUF, 2 * 1024 * 1024
        )  # 2MB 发送缓冲区
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024
        )  # 2MB 接收缓冲区
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # 启用TCP Keepalive

        local_ip = get_local_ip()

        if password:
            print("访问密码已设置")
            logging.info("访问密码已设置")

        print(f"正在共享文件夹: {os.getcwd()}")
        logging.info(f"正在共享文件夹: {os.getcwd()}")

        print(f"本地访问: {scheme}://localhost:{port}")
        logging.info(f"本地访问: {scheme}://localhost:{port}")

        print(f"局域网访问: {scheme}://{local_ip}:{port}")
        logging.info(f"局域网访问: {scheme}://{local_ip}:{port}")

        if scheme == "https":
            print("使用自签名证书，浏览器将显示安全警告，请点击“高级” → “继续访问”")
            logging.info("使用自签名证书，浏览器将显示安全警告")

        print(f"缓存统计: {scheme}://localhost:{port}/cache-stats")
        logging.info(f"缓存统计: {scheme}://localhost:{port}/cache-stats")

        print(f"清空缓存: {scheme}://localhost:{port}/cache-clear")
        logging.info(f"清空缓存: {scheme}://localhost:{port}/cache-clear")

        print(
            f"配置缓存: {scheme}://localhost:{port}/cache-config?timeout={CACHE_TIMEOUT}&capacity={CACHE_CAPACITY}"
        )
        logging.info(
            f"配置缓存: {scheme}://localhost:{port}/cache-config?timeout={CACHE_TIMEOUT}&capacity={CACHE_CAPACITY}"
        )
        
        print("按 Ctrl+C 停止服务器")

        # 启动服务器并保持运行e)
        server.serve_forever()

    except (ValueError, PermissionError) as e:
        print(f"错误: {e}")
        logging.error(f"错误: {e}")
    except KeyboardInterrupt:
        print("\n服务器已停止")
        logging.info("服务器已停止")
    except Exception as e:
        print(f"服务器错误: {e}")
        logging.error(f"服务器错误: {e}")


def main():
    """主函数，解析命令行参数并启动服务器"""
    # 设置日志
    log_file = setup_logging()
    logging.info("Share 文件服务器启动")

    parser = argparse.ArgumentParser(
        description="启动一个简单的HTTP服务器提供本地文件夹服务"
    )
    parser.add_argument("folder", help="要提供服务的文件夹路径")
    parser.add_argument("--password", action="store_true", help="启用密码并提示输入")
    parser.add_argument(
        "--https", action="store_true", help="启用 HTTPS（自动生成自签名证书）"
    )
    parser.add_argument(
        "--cert", type=str, default=None, help="HTTPS 证书文件路径（.crt 或 .pem）"
    )
    parser.add_argument(
        "--key", type=str, default=None, help="HTTPS 私钥文件路径（.key）"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8000, help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="服务器监听地址 (默认: 0.0.0.0 - 所有接口)"
    )
    parser.add_argument(
        "--debug-cache", action="store_true", help="在页面底部显示缓存统计信息"
    )
    parser.add_argument(
        "--cache-timeout",
        type=int,
        default=CACHE_TIMEOUT,
        help=f"缓存超时时间（秒）(默认: {CACHE_TIMEOUT})",
    )
    parser.add_argument(
        "--cache-capacity",
        type=int,
        default=CACHE_CAPACITY,
        help=f"缓存最大容量 (默认: {CACHE_CAPACITY})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="显示版本信息并退出",
    )

    args = parser.parse_args()

    # 获取密码
    password = None
    if args.password:
        password = getpass.getpass("请输入访问密码: ")

    # HTTPS 证书处理
    cert_file = args.cert
    key_file = args.key

    if args.https:
        if not cert_file or not key_file:
            # 自动管理证书
            cert_file, key_file = ensure_ssl_cert()
        # 验证文件存在
        if not os.path.exists(cert_file):
            print(f"错误：证书文件不存在: {cert_file}")
            sys.exit(1)
        if not os.path.exists(key_file):
            print(f"错误：私钥文件不存在: {key_file}")
            sys.exit(1)

    # 设置环境变量以启用缓存调试
    if args.debug_cache:
        os.environ["DEBUG_CACHE"] = "1"

    # 配置缓存参数
    FileServerHandler.cache.timeout = args.cache_timeout
    FileServerHandler.cache.capacity = args.cache_capacity

    # 启动服务器
    serve_folder(
        args.folder,
        args.port,
        args.host,
        password,
        cert_file=cert_file if args.https else None,
        key_file=key_file if args.https else None,
    )


if __name__ == "__main__":
    main()
