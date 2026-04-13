# Pic2Pic

一个基于 Stable Diffusion + ControlNet 的草图到图像（Scribble-to-Image）原型项目。

当前仓库包含：

- 命令行离线推理流程（`main.py`）
- Flask 后端服务（`server.py`）
- Web 画布前端（`web/index.html`）

## 文档导航

- 交接总文档（建议先读）：`doc/project_handover.md`
- Web UI 专项说明：`doc/web_ui.md`
- 输入画布早期原型：`doc/input_canvas_prototype.md`

## 快速开始

1. 安装依赖（建议在虚拟环境中）
2. 准备模型文件（见 `doc/project_handover.md` 的“模型文件准备”）
3. 启动服务：`python server.py`
4. 打开浏览器：`http://127.0.0.1:5000/`

## 当前状态

- ✅ 两阶段推理（Stage1 LCM + Stage2 DPMPP）已接通
- ✅ Web 端绘图、自动预览、生成流程已打通
- ✅ NSFW 基础拦截策略已接入
