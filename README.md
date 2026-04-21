# Pic2Pic

一个基于 Stable Diffusion + ControlNet 的交互式“草图到图像”（Scribble-to-Image）原型项目。支持实时草图引导、两阶段图像生成及多种风格微调。

---

## 📂 项目结构

项目已完成模块化重构，主要分为以下核心部分：

*   **`web/backend/`**: 基于 Flask 的后端推理服务。
    *   `server.py`: 提供 Web API 接口。
    *   `main.py`: 核心推理逻辑实现（支持 LCM 与 DPMPP 两阶段推理）。
*   **`web/frontend/`**: 基于 Vue 3 + Vite 的现代交互前端。
    *   提供高性能画布、实时预览、风格选择器及进度监控。
*   **`models/`**: 模型存储目录（需要手动准备权重文件）。
*   **`doc/`**: 详细的设计文档与技术交接说明。

---

## 🚀 快速开始

### 1. 准备模型文件 (必须)
请下载以下模型并放入对应目录（文件名需与代码默认值一致）：

| 模型类型 | 目标路径 | 推荐来源 |
| :--- | :--- | :--- |
| **SD Checkpoint** | `models/checkpoints/dreamshaper_8.safetensors` | Civitai / HuggingFace |
| **ControlNet Scribble** | `models/controlnet/control_v11p_sd15_scribble.pth` | lllyasviel/ControlNet-v1-1 |
| **ControlNet Canny** | `models/controlnet/control_v11p_sd15_canny.pth` | lllyasviel/ControlNet-v1-1 |

### 2. 启动后端服务
```bash
# 建议在虚拟环境中操作
cd web/backend
pip install -r requirements.txt
python server.py
```
后端默认运行在 `http://127.0.0.1:5000`。

### 3. 启动前端界面
```bash
cd web/frontend
npm install
npm run dev
```
访问 `http://localhost:5173` 即可进入交互界面。

---

## ✨ 当前状态与特性

- [x] **两阶段生成工作流**: 
    - **Stage 1 (LCM)**: 提供极速的低步数预览。
    - **Stage 2 (DPMPP)**: 自动执行高品质图像细化。
- [x] **实时进度追踪系统**:
    - 后端步进回调（Callback）实时反馈推理状态。
    - 前端轮询机制，配合 **高级毛玻璃质感进度条** 提供丝滑视觉体验。
- [x] **高级结果展示**:
    - 引入 **Result Modal (结果弹窗)**，集中展示预览图、边缘检测图及最终高清图。
    - 优化页面布局，实现“即画即得”的高效交互工作流。
- [x] **现代 Web 交互**:
    - 响应式画布，支持缩放、撤销及压力感应模拟。
    - 修复了 Canny 边缘提取逻辑及资源跨域代理问题。
- [x] **内容增强**:
    - 内置 8 种高频风格预设，支持 4 种 LoRA 模型及其权重调节。

---

## 📖 文档导航

*   **[项目交接总文档](file:///f:/github/Pic2Pic/doc/project_handover.md)** (建议首次阅读)
*   **[Web UI 专项说明](file:///f:/github/Pic2Pic/doc/web_ui.md)**
*   **[前端开发指南](file:///f:/github/Pic2Pic/web/frontend/README.md)**

---

## 📄 许可证

本项目仅供学习与原型展示使用。模型权重请遵循相关原作者的许可证要求。
