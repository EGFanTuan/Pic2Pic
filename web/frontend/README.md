# Pic2Pic Web UI (Vue 3 + Vite)

[![Vue](https://img.shields.io/badge/Vue.js-3.4-4fc08d?logo=vue.js)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff?logo=vite)](https://vitejs.dev/)
[![Pinia](https://img.shields.io/badge/Pinia-2.1-yellow?logo=pinia)](https://pinia.vuejs.org/)

这是 Pic2Pic 项目的现代 Web 前端。基于 **Vue 3** 和 **Vite** 构建，旨在为用户提供一个响应迅速、功能丰富且直观的“草图到图像”（Scribble-to-Image）交互界面。

---

## 🌟 核心特性

### 🎨 强大交互式画布
*   **平滑缩放**: 支持从 25% 到 300% 的无级缩放，完美处理细节。
*   **快捷操作**: 
    *   `B` - 切换画笔 | `E` - 切换橡皮擦
    *   `Ctrl + Z` - 撤销历史 | `Ctrl + 0` - 重置缩放
    *   `鼠标滚轮` - 动态缩放
*   **绘图辅助**: 动态调节画笔粗细（1-50px），支持多达 50 步的撤销操作。
*   **资产管理**: 支持一键上传背景图及导出创作内容。

### 🎛️ 智能控制面板
*   **双层交互**: 基础模式（简洁高效）与高级模式（精细微调）一键切换。
*   **实时响应**: 参数变更触发智能预览，所见即所得。
*   **质量预设**: 针对不同需求内置了 Noob、Normal、Hardcore、God 四档预设方案。

### 🎭 创作增强
*   **风格预设**: 内置 8 种高频风格（动漫、写实、赛博朋克等），自动注入提示词。
*   **LoRA 融合**: 支持 4 种 LoRA 模型，并提供 0-1 的权重精细调节。

### 📊 全流程监控
*   **实时进度条**: 百分比进度显示，配合平滑动画。
*   **阶段反馈**: 清晰展示当前处于 LCM 预览或 DPMPP 优化阶段。

---

## 🛠️ 技术架构

### 技术栈
*   **核心框架**: Vue 3 (Composition API)
*   **状态管理**: Pinia (模块化、响应式)
*   **网络请求**: Axios (拦截器、取消请求支持)
*   **构建工具**: Vite 5 (极致的开发热重载)
*   **设计语言**: 现代、简洁的响应式 UI 布局

### 目录结构
```text
web/frontend/
├── src/
│   ├── components/       # UI 核心组件
│   │   ├── CanvasComponent.vue  # 绘图引擎
│   │   ├── ControlPanel.vue     # 参数控制
│   │   ├── PreviewPanel.vue     # 结果展示
│   │   ├── StyleSelector.vue    # 风格/LoRA 切换
│   │   └── ProgressBar.vue      # 任务状态
│   ├── stores/          # 全局状态管理 (api.js)
│   ├── App.vue          # 应用入口
│   └── main.js          # 初始化配置
├── index.html           # 页面模板
└── vite.config.js       # 构建及代理配置
```

---

## 🚀 快速开始

### 前置条件
*   **Node.js**: 16.0 或更高版本
*   **后端服务**: 确保后端 API 运行在 `http://127.0.0.1:5000`

### 安装与运行
1.  **进入前端目录**:
    ```bash
    cd web/frontend
    ```
2.  **安装依赖**:
    ```bash
    npm install
    ```
3.  **启动开发服务器**:
    ```bash
    npm run dev
    ```
    访问 `http://localhost:5173` 即可开始创作。

### 生产环境构建
```bash
npm run build
```
静态资源将输出至 `dist/` 目录。

---

## 🔌 API 接口集成

前端通过 Vite 代理将 `/api` 路径转发至后端服务。主要交互路径：
*   `GET /status`: 检查后端 GPU/模型状态。
*   `POST /preview`: 生成快速低步数预览。
*   `POST /generate`: 执行高品质最终生成。

---

## 📅 路线图

- [ ] 增加更多高品质风格预设。
- [ ] 允许用户自定义上传 LoRA 模型。
- [ ] 增加批量图像生成与历史记录对比。
- [ ] 支持 I18n 多语言国际化。

---

## 📄 许可证

本项目遵循 Pic2Pic 主项目的开源协议。
