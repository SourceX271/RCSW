# RCSW — Remove CamScanner Watermark

> [!TIP]
>
> 如果你被扫描全能王的水印折磨过，那么恭喜你发现了这个软件


RCSW 是一款专门用于去除「扫描全能王」（CamScanner）生成 PDF 文件水印的桌面工具。针对扫描全能王的特定水印格式进行了优化，能够精准识别并去除水印图标，同时完整保留扫描图片内容。

## 特性

- 批量处理多个 PDF 文件
- 智能水印检测算法（尺寸过滤 + 位置匹配 + 跨页一致性）
- 5 种缩放模式：填充整页、适应页面、拉伸、适应宽度、适应高度
- 4 档输出质量：低 / 中 / 高 / 原图
- 可调节 DPI 和 JPEG 质量
- 支持拖拽添加文件
- Windows 11 Mica 亚克力毛玻璃效果
- 浅色 / 深色 / 跟随系统 主题
- 处理完成后自动打开输出目录

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| GUI | PySide6 + PySide6-Fluent-Widgets |
| PDF处理 | PyMuPDF (fitz) |
| 图像处理 | Pillow |
| 构建 | Nuitka |

### 依赖树状图
```
rcsw
├── nuitka v4.1.3
├── pillow v12.2.0
├── pymupdf v1.27.2.3
├── pyside6 v6.11.1
│   ├── pyside6-addons v6.11.1
│   │   ├── pyside6-essentials v6.11.1
│   │   │   └── shiboken6 v6.11.1
│   │   └── shiboken6 v6.11.1
│   ├── pyside6-essentials v6.11.1 (*)
│   └── shiboken6 v6.11.1
└── pyside6-fluent-widgets v1.11.2
    ├── darkdetect v0.8.0
    ├── pyside6 v6.11.1 (*)
    └── pysidesix-frameless-window v0.8.1
        └── pywin32 v312
```

## 安装和运行
### 下载安装包
1. 点击右侧 Releases 打开发行版页面
2. 找到最新版本
3. 选择适合你的安装包或压缩包

### 从源代码运行

Git 克隆
```bash
git clone https://github.com/SourceX271/RCSW.git
cd RCSW
```
安装依赖
```bash
uv sync
```
 运行
```bash
uv run main.py
```

## 构建 Windows EXE

```bash
.\build.ps1
```

构建产物输出到 `dist/` 目录。

## 版本和兼容性

该软件发行版本命名为 `XX.YY.ZZ`  
- `XX` 表示大版本号，如果是 `0` 表示软件还处于最终测试阶段
- `YY` 表示新功能添加
- `ZZ` 表示 Bug 修复和软件优化

> [!NOTE]
>
> 一般只有在重大功能增加和严重 Bug 修复和大版本更新才会提供 macOS 和 Linux 版本  
> Windows 版本仅 Windows10 及以上可用
## 报告 Bug 或提出建议
你的经验和建议是我和我的软件进步的动力，如果你遇到了 Bug 或你有一些好建议，欢迎随时提出


### 报告 Bug  
1. 导出日志
   - 如果软件可以打开就到 "设置 -> 日志 -> 导出日志"
   - 如果软件无法打开就到 
     - `C:\Users\你的用户名\AppData\RCSW\logs` 把 `rcsw.log` 找到
     - 按下 `Win + R` 打开运行窗口，输入 `%USERPROFILE%\AppData\RCSW\logs` 后点击确定，把 `rcsw.log` 找到
2. 把导出的日志和遇到的 Bug 发给作者

### 联系作者
- 发邮件至 `860256007@qq.com` 或 `liyichen314@outlook.com`
- 点击上方 `Issues` 提出 Bug 或建议
- 到作者 [bilibili 首页](https://space.bilibili.com/3461569679722999) 随便找一个与这个软件相关的视频评论或私信

## 许可证

GNU General Public License v3.0
