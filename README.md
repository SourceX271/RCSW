# RCSW — Remove CamScanner Watermark

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

## 安装

```bash
git clone https://github.com/SourceX271/RCSW.git
cd RCSW
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 构建 Windows EXE

```bash
.\build.ps1
```

构建产物输出到 `dist/` 目录。

## 许可证

GNU General Public License v3.0
