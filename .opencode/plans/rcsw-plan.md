# RCSW (Remove CamScanner Watermark) 开发方案

## 1. 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Python | CPython | 3.14.5 |
| GUI框架 | PySide6 + PySide6-Fluent-Widgets | 6.11.1 / 1.11.2 |
| PDF处理 | PyMuPDF (fitz) | 1.27.2.3 |
| 图片处理 | Pillow | 12.2.0 |
| 打包 | Nuitka | 需安装 |

## 2. 文件结构

```
RCSW/
├── main.py                    # 入口文件
├── pyproject.toml             # 项目配置(pip install -e .)
├── rcsw/
│   ├── __init__.py
│   ├── app.py                 # QApplication 创建 + Fluent 主题初始化
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py     # 主窗口 (继承 FluentWindow)
│   │   ├── file_panel.py      # 文件拖放选择区域
│   │   ├── settings_panel.py  # 设置面板 (DPI/质量/水印检测参数)
│   │   ├── preview_panel.py   # 前后对比预览
│   │   └── style.py           # Fluent 样式微调
│   ├── core/
│   │   ├── __init__.py
│   │   ├── detector.py        # 水印自动检测算法
│   │   ├── processor.py       # PDF 处理引擎
│   │   └── worker.py          # QThread 后台处理线程
│   └── resources/
│       └── icon.svg           # 应用图标
```

## 3. 核心算法

### 3.1 水印自动检测 (detector.py)

扫描全能王水印特征分析：
- 每页PDF包含2张图片：1张大图（扫描内容）+ 1张小图（水印logo）
- 水印图尺寸约 260×260 像素
- 水印固定在页面特定角落

**检测策略（多层判断）：**

```
层级1 — 尺寸过滤：
  宽度 < max_wm_size (默认500px) AND 高度 < max_wm_size → 候选水印

层级2 — 跨页一致性：
  同一xref（图片引用）出现在多页 → 大概率是水印
  
层级3 — 位置判断：
  相对于页面边缘的距离判断属于哪个角落
  (右下/左下/右上/左上/底部居中/平铺)

层级4 — 占比分析：
  水印面积占比 < 阈值 (默认5%) → 最终确认
```

### 3.2 PDF 处理流程 (processor.py)

```
1. 打开源PDF
2. 对每一页：
   a. 获取所有图片及其位置
   b. 调用 detector 识别水印图片索引
   c. 提取主图片（非水印图片中最大的那张）
   d. 用 Pillow 处理图片：
      - 保持长宽比缩放至整页 (Aspect Fit → Center Crop)
      - 转换为 RGB 模式
      - 按用户设定DPI和JPEG质量编码
   e. 创建新页面，插入处理后的图片
3. 保存新PDF
4. 返回结果统计
```

### 3.3 图片缩放逻辑 (保持长宽比缩放至整页)

```
page_aspect = page_w / page_h
img_aspect = img_w / img_h

if img_aspect > page_aspect:
    scaled_h = target_h
    scaled_w = img_w * (target_h / img_h)
else:
    scaled_w = target_w
    scaled_h = img_h * (target_w / img_w)

crop_x = (scaled_w - target_w) // 2
crop_y = (scaled_h - target_h) // 2
```

## 4. UI 设计 (Fluent Design)

### 4.1 主窗口布局

```
+----------------------------------------------------------+
|  RCSW - Remove CamScanner Watermark             - □ ×    |
+----------------------------------------------------------+
|  [左侧导航]        [内容区域]                             |
|  +----------+  +--------------------------------------+  |
|  |   文件   |  |  文件列表                              |  |
|  |   设置   |  |  +----------------------------------+  |  |
|  |   预览   |  |  | □ 文件1.pdf  26页 15.2MB         |  |  |
|  |          |  |  | □ 文件2.pdf  10页  8.1MB         |  |  |
|  |          |  |  +----------------------------------+  |  |
|  |          |  |  [添加文件] [清空列表]                 |  |
|  +----------+  +--------------------------------------+  |
|                                                          |
|  状态栏: 就绪 | 已选择 2 个文件                           |
+----------------------------------------------------------+
|  ============================ 60%  处理中... [取消]      |
+----------------------------------------------------------+
```

### 4.2 各面板功能

**文件面板 (FilePanel)**
- 拖放区域 (QDragEnterEvent)
- 批量文件选择按钮
- 文件列表 (QListWidget，显示文件名/页数/大小)
- 单个移除 / 全部清空

**设置面板 (SettingsPanel)**
- 输出DPI: QSlider (72–600, 默认200) + SpinBox
- JPEG质量: QSlider (50–100, 默认95) + SpinBox
- 最大水印尺寸阈值: QSlider (100–1000, 默认500) + SpinBox
- 水印位置: QComboBox (自动检测/右下角/左下角/右上角/左上角/底部居中)
- 输出目录: QLineEdit + 浏览按钮 (默认: 源文件同目录)
- 保持长宽比缩放: QCheckBox (默认勾选)

**预览面板 (PreviewPanel)**
- 左右分栏: 原图 vs 处理后
- 底部导航: 上一页/下一页 + 页码显示
- 仅在选中单个文件时可用

## 5. 线程模型

```
UI主线程:
  +-- 文件管理、设置变更、预览渲染
  +-- 启动/取消 ProcessingWorker

ProcessingWorker (QThread):
  +-- 逐页处理 PDF
  +-- 通过信号 report progress (current, total, filename)
  +-- 通过信号 report finished (success/error)
  +-- 支持取消 (isInterruptionRequested)
```

## 6. 打包 (Nuitka)

```powershell
pip install nuitka

python -m nuitka --standalone --windows-console-mode=disable `
  --enable-plugin=pyside6 `
  --include-package=rcsw `
  --output-dir=dist `
  --windows-icon-from-ico=rcsw/resources/icon.ico `
  main.py
```

关键配置:
- `--standalone`: 独立文件夹分发
- `--windows-console-mode=disable`: 无控制台窗口
- `--enable-plugin=pyside6`: PySide6 支持
- 不推荐 `--onefile` (PySide6+Fluent 解压慢且杀软误报率高)

## 7. 依赖清单 (pyproject.toml)

```toml
[project]
name = "rcsw"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "PySide6>=6.5",
    "PySide6-Fluent-Widgets>=1.5",
    "PyMuPDF>=1.23",
    "Pillow>=10.0",
]

[project.scripts]
rcsw = "rcsw.app:main"
```

## 8. 关键设计决策

| 决策 | 理由 |
|------|------|
| 使用 FluentWindow 而非普通 QMainWindow | 符合 WinUI3 风格，内置导航栏/状态栏 |
| 每页重建新PDF (丢弃原文本层) | 扫描全能王PDF不含可搜索文本，只有图片 |
| 处理输出为JPEG流 | 平衡质量与文件大小 |
| 线程使用 QThread + moveToThread | 稳定，支持取消和进度报告 |
| 预览仅限单文件 | 批量时预览无意义 |
| 跨页检查水印一致性 | 提高自动检测准确率 |