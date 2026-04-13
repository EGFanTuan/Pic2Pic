# Pipeline 深入说明, 负责调优和尝试加入LoRA的话最好看一看

## 1. 为什么是“两阶段流程”

当前流程不是一次性直接出 final，而是拆成：

1. Stage1（LCM + Dual ControlNet）
2. latent 上采样
3. Stage2（DPMPP + Scribble ControlNet）

这样设计的核心原因：

- **交互速度**：Stage1 步数少（默认 4），可快速给预览
- **结构稳定**：草图结构先被锁定，再做质量增强
- **质量提升**：Stage2 用更多步数（默认 35）细化纹理和光影
- **调参可分层**：结构相关参数和细节相关参数可以分开调

---

## 2. 从代码看完整数据流

关键实现分布：

- `src/pipeline.py`：模型和调度器构建
- `server.py`：请求解析、Stage1/Stage2 执行、输出落盘
- `src/latent_utils.py`：latent 上采样
- `src/image_utils.py`：输入预处理

### 2.1 Pipeline 构建 (`src/pipeline.py`)

`buildPipeline(...)` 当前做了这些事：

1. 加载两个 ControlNet：
   - `control_v11p_sd15_scribble.pth`
   - `control_v11p_sd15_canny.pth`
2. 用 checkpoint + 双 ControlNet 构建 `StableDiffusionControlNetPipeline`
3. 复制组件构建 `StableDiffusionControlNetImg2ImgPipeline` 作为 Stage2
4. Stage1 scheduler 设为 `LCMScheduler`
5. Stage2 scheduler 设为 `DPMSolverMultistepScheduler(use_karras_sigmas=True)`
6. CUDA 情况下启用 TF32、尝试 `xformers`、VAE tiling

### 2.2 Stage1 (`server.py::run_stage1`)

输入：

- 草图图像 `control_image`
- 文本提示词（正/负）
- Stage1 参数（步数、guidance、denoise、双 ControlNet scale）

主要步骤：

1. 图像 resize 到目标分辨率
2. `invertImage` 做反色（当前流程约定）
3. 生成 Scribble / Canny 控制图
4. 生成随机噪声 latent 作为初始输入
5. 调用 Stage1 pipeline，`output_type='latent'`
6. 拿到：
   - `latents_stage1`
   - `stage1_decoded`（预览图）
   - `nsfw_flag`

输出：

- `latents_stage1`（给 Stage2 用）
- Stage1 预览图
- Canny 图（用于可视化）
- NSFW 标记

### 2.3 latent 上采样 (`src/latent_utils.py`)

- 当前方法：`torch.nn.functional.interpolate`
- 默认倍率：`1.5`
- 默认模式：`nearest-exact`（内部映射为 `nearest`）

作用：

- 在 latent 空间放大，再做二阶段重绘
- 相比直接在像素空间放大，通常更省且更贴合扩散流程

### 2.4 Stage2 (`server.py::run_stage2`)

输入：

- `latents_stage1`（上采样后）
- Scribble 控制图（按新分辨率 resize）
- Stage2 参数（steps/guidance/denoise/scale）

主要步骤：

1. 上采样后的 latent 作为 img2img 输入
2. 仅使用 Scribble ControlNet（当前 Stage2 不使用 Canny）
3. DPMPP 多步采样精修
4. 得到 final image + NSFW 标记

输出：

- Final 图
- Stage2 NSFW 标记

---

## 3. 每一块“干什么 + 为什么”

## 3.1 Scribble ControlNet

- 干什么：约束整体轮廓、主体结构
- 为什么：草图任务核心就是“别偏构图”

## 3.2 Canny ControlNet（仅 Stage1）

- 干什么：补充边缘细节约束
- 为什么只在 Stage1：先快速稳定结构，Stage2 避免过度约束导致“僵化”

> 当前实现中 `cannyPreprocessor` 为占位，后续可以评估是否真的需要 Canny 约束

## 3.3 LCM（Stage1）

- 干什么：快速采样，适合高频预览
- 为什么：Web 交互对延迟敏感，先快后精修比一把梭更实用

## 3.4 DPMPP（Stage2）

- 干什么：在可控范围内提升细节和质感
- 为什么：相比 LCM，更适合高质量最终输出

## 3.5 NSFW 前缀与拦截

- 干什么：基础安全保护(因为没有加载safety checker所以可能并没有太大用处)
- 为什么：当前是可上线原型，先保证最小可用安全策略

> 后续的优化点之一

---

## 4. LoRA 集成建议（不改架构前提(改架构当然也可以, 效果不变差就行w)）

- LoRA的作用原理，效果和使用方式可以去问问AI
- 没有太多建议, 因为我还没试过;w;
- 所以你可以都试试怎么集成进来效果最好

---

## 5. 参数调优建议

- 可以先了解一下每个参数大概干什么用w
- 主要可能是再找找加了LoRA之后的预设吧, 大概就是两个controlNet的scale
- 还有LoRA的强度
- 其他的大概没什么可调了我觉得
- 调参前固定好一个种子w 不然就没法对比了

---

## 6. 当前流程的已知技术债

1. `cannyPreprocessor` 为占位实现
2. 无任务队列（并发体验受限）
3. 安全策略仍偏基础（依赖 pipeline 返回标记）
4. 参数没有按“场景包”沉淀（建议后续做 preset profile）

## 7. 有问题随时问(问AI可能会更快w)
