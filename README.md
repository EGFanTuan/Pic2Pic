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
```
## 7.3 模型文件准备（必须）

请自行下载并放入以下目录（仓库不提交模型权重）：

- 主模型 checkpoint：
  - 目标路径：`models/checkpoints/dreamshaper_8.safetensors`
  - 对应参数：`--checkpoint_name dreamshaper_8.safetensors`

- ControlNet Scribble：
  - 目标路径：`models/controlnet/control_v11p_sd15_scribble.pth`

- ControlNet Canny：
  - 目标路径：`models/controlnet/control_v11p_sd15_canny.pth`

> 以上文件名来自当前代码默认值；若改名，请同步调整启动参数或代码配置。
> 实在下载不了可以弄个U盘来找我拷一份
> 模型去哪下都一样, 应该没有盗版这一说
```
3. 启动服务：`python server.py`
4. 打开浏览器：`http://127.0.0.1:5000/`

## 当前状态

- ✅ 两阶段推理（Stage1 LCM + Stage2 DPMPP）已接通
- ✅ Web 端绘图、自动预览、生成流程已打通
- ✅ NSFW 基础拦截策略已接入
