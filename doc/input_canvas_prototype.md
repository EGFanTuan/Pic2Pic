# 输入画布原型

已提供一个可直接打开的原型页面：`doc/input_canvas_prototype.html`

## 功能

- 固定画布尺寸：`400 x 600`（与 `src/config.py` 默认 `--width/--height` 一致）
- 画线（黑色画笔）
- 橡皮擦
- 撤销（最多保留 50 步）
- 清空画布
- 下载 PNG（建议文件名：`scribble_input.png`）

## 使用方式

1. 在浏览器中打开 `doc/input_canvas_prototype.html`
2. 绘制线稿后点击“下载 PNG”
3. 将导出的图片放入项目的 `input/` 目录
4. 运行 `main.py`，程序会从 `input/` 读取图片并处理

## 说明

这个页面是“输入部分”的最小原型，不依赖任何前端框架，也不改动现有 Python 推理逻辑。
