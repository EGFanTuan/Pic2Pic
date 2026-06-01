# Pic2Pic

一个基于 **Stable Diffusion + ControlNet** 的交互式「草图到图像」(Scribble-to-Image) 原型项目。支持实时草图引导、两阶段图像生成及多种风格微调。

---

## 📂 项目结构

项目已完成模块化重构，主要分为以下核心部分：

| 目录 | 说明 | 核心文件 |
| :--- | :--- | :--- |
| **`web/backend/`** | Flask 后端推理服务 | `server.py` (API接口), `main.py` (推理逻辑) |
| **`web/frontend/`** | Vue 3 + Vite 交互前端 | `App.vue` (主应用), `CanvasComponent.vue` (画布) |
| **`models/`** | 模型权重存储目录 | 需要手动准备 |
| **`scripts/`** | 快捷启动脚本 | `start_project.ps1` (Windows) |
| **`doc/`** | 设计文档 | 技术说明与交接文档 |

---

## 🚀 快速开始

### 1. 准备模型文件 (必须)

请下载以下模型并放入对应目录：

| 模型类型 | 目标路径 | 推荐来源 |
| :--- | :--- | :--- |
| **SD Checkpoint** | `models/checkpoints/dreamshaper_8.safetensors` | [Civitai](https://civitai.com/) / HuggingFace |
| **ControlNet Scribble** | `models/controlnet/control_v11p_sd15_scribble.pth` | [lllyasviel/ControlNet-v1-1](https://huggingface.co/lllyasviel/ControlNet-v1-1) |
| **ControlNet Canny** | `models/controlnet/control_v11p_sd15_canny.pth` | [lllyasviel/ControlNet-v1-1](https://huggingface.co/lllyasviel/ControlNet-v1-1) |

### 2. 一键启动 (推荐)

**Windows 用户**：
```powershell
.\scripts\start_project.ps1
```

该脚本会自动：
- 创建并激活虚拟环境
- 安装所需依赖
- 启动后端服务
- 启动前端开发服务器

### 3. 手动启动

**启动后端服务**：
```bash
cd web/backend
pip install -r requirements.txt
python server.py
```
后端默认运行在 `http://127.0.0.1:5000`

**启动前端界面**：
```bash
cd web/frontend
npm install
npm run dev
```
访问 `http://localhost:5173` 即可进入交互界面

---

## 🎨 使用指南

### 画布操作

| 操作 | 快捷键 | 说明 |
| :--- | :--- | :--- |
| 画笔工具 | `B` | 切换到画笔模式 |
| 橡皮擦 | `E` | 切换到橡皮擦模式 |
| 撤销 | `Ctrl + Z` | 撤销上一步操作 |
| 清空画布 | 🗑️ 按钮 | 清除所有绘制内容 |
| 上传图片 | 📁 按钮 | 上传参考图片 |
| 下载画布 | 💾 按钮 | 导出当前画布 |

### 尺寸调整

- 在右侧控制面板中直接输入宽度和高度（建议为8的倍数）
- 支持预设质量模式选择
- 默认尺寸：512 × 768（平衡速度与质量）

### 生成流程

1. **绘制草图**：在左侧画布上绘制您的创意
2. **自动预览**：绘制停止后1.5秒自动生成预览
3. **手动预览**：点击「预览」按钮手动触发预览
4. **生成图像**：点击「生成」按钮生成最终高清图像

### 两阶段生成

| 阶段 | 模型 | 特点 |
| :--- | :--- | :--- |
| **Stage 1** | LCM (Latent Consistency Model) | 极速预览，低步数推理 |
| **Stage 2** | DPMPP | 高品质细化，完整步数 |

---

## ✨ 特性亮点

### 已实现功能

- [x] **两阶段生成工作流**：LCM快速预览 + DPMPP高质量细化
- [x] **实时进度追踪**：毛玻璃质感进度条，实时反馈推理状态
- [x] **智能预览系统**：绘制完成后自动触发预览，支持手动预览
- [x] **现代交互画布**：支持缩放、撤销、画笔大小调节
- [x] **风格预设**：内置8种高频艺术风格一键切换
- [x] **LoRA支持**：支持4种LoRA模型及其权重调节
- [x] **响应式布局**：自适应窗口大小，优化空间利用
- [x] **GPU/CPU切换**：支持硬件加速模式切换

### 技术栈

| 分类 | 技术 | 版本 |
| :--- | :--- | :--- |
| 前端框架 | Vue | 3.x |
| 构建工具 | Vite | 6.x |
| 状态管理 | Pinia | 2.x |
| 后端框架 | Flask | 2.x |
| AI框架 | PyTorch | 2.x |
| 扩散模型 | diffusers | 0.x |

---

## 📝 API 接口

### POST /api/generate

生成图像的主接口

**请求参数**：
```json
{
  "image": "base64_encoded_image",
  "width": 512,
  "height": 768,
  "prompt": "beautiful landscape",
  "negative_prompt": "ugly, blurry",
  "seed": 143,
  "output_format": "png"
}
```

**响应**：
```json
{
  "stage1_url": "/outputs/stage1_xxx.png",
  "canny_url": "/outputs/canny_xxx.png",
  "final_url": "/outputs/final_xxx.png"
}
```

### POST /api/preview

快速预览接口

### GET /api/status

获取服务状态

---

## 🔧 配置说明

### 后端配置 (`web/backend/config.py`)

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `DEVICE` | `cuda` | 推理设备 (cuda/cpu) |
| `OUTPUT_DIR` | `outputs/` | 输出目录 |
| `MAX_WIDTH` | `768` | 最大宽度 |
| `MAX_HEIGHT` | `1024` | 最大高度 |

### 前端环境变量 (`web/frontend/.env`)

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:5000` | 后端API地址 |

---

## ❓ 常见问题

### Q: 模型下载失败怎么办？

A: 请确保网络通畅，或手动下载模型放入指定目录。推荐使用国内镜像站。

### Q: 生成速度很慢？

A: 
- 检查是否启用了GPU加速（页面右上角显示GPU）
- 尝试减小画布尺寸
- 确保已安装CUDA及cuDNN

### Q: 画布无法绘制？

A: 
- 检查浏览器控制台是否有报错
- 确保画布区域已正确加载
- 尝试刷新页面重新加载

### Q: 预览图不显示？

A: 
- 检查后端服务是否正常运行
- 检查浏览器开发者工具的网络请求
- 确认模型文件路径正确

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发规范

1. 代码风格遵循项目现有约定
2. 提交前确保通过 lint 检查
3. 新增功能请添加相应测试

### 目录结构约定

```
.
├── doc/              # 文档
├── models/           # 模型文件（需手动下载）
├── scripts/          # 脚本
└── web/
    ├── backend/      # 后端代码
    └── frontend/     # 前端代码
```

---

## 📄 许可证

本项目仅供学习与原型展示使用。模型权重请遵循相关原作者的许可证要求。

---

## 📧 联系方式

如有问题或建议，欢迎提交 Issue 或邮件联系。