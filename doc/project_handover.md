# 交接文档

> 用于快速理解当前项目进度与代码结构。

## 1. 项目当前目标与边界

### 1.1 当前已完成的核心能力

- Web 画布输入（画笔、橡皮擦、撤销、清空、下载、上传）
- 后端服务化推理接口（预览 + 正式生成）
- 两阶段生成流程：
  - Stage1：LCM（快速预览）
  - Stage2：DPMPP（质量增强）
- 基础安全策略：
  - 负向提示词强制前缀（NSFW 相关）
  - Stage1/Stage2 结果 NSFW 标记拦截
- 前端自动预览（防抖）、普通/高级参数模式
- 默认参数与普通模式预设由服务端统一下发

### 1.2 当前不在“已完成”范围内（后续可做）

- 多任务队列与进度轮询（当前是单飞行锁，忙时返回 429）
- 完整用户历史记录存储
- 更独立、稳定的 NSFW 分类器
- 风格模板系统（Prompt/LoRA 组合的一键切换）
- 更好的画布(现在这个太丑陋了;w;)
- 更好的前端页面
- 更好的后端
- 任何 想加的/好玩的/有用的/能加分的/性能优化 功能

---

## 2. 工作流说明

> pipeline详细说明见 pipeline_deep_dive.md

## 2.1 整体流程

1. 用户在网页画布画草图（默认白底黑线）(强制白底黑线！！别问, 问就是这么设计的, 不然controlNet又哭又闹)(当然如果你想把彩色图也加入支持那你来做我没意见😀)
2. 前端将画布导出 PNG，连同参数 JSON 发给后端
3. 后端执行两阶段推理：
   - Stage1：快速出结构预览（并返回 Stage1 图）
   - Stage2：基于 Stage1 latent 放大+精修得到 final
4. 后端把结果图写入 `output/`，前端通过 `/outputs/<filename>` 回显

## 2.2 两阶段设计的意义

- Stage1 快：便于实时预览和快速试错
- Stage2 稳：在结构不丢失的前提下提高画面质量
- 综合体验优于单阶段“要么快要么好”的二选一

## 2.3 当前 Control 信号来源

- Scribble：来自输入草图（反色 + 预处理）
- Canny：接口与参数已预留

> 注意：当前 `src/image_utils.py` 中 `cannyPreprocessor` 是直通返回（未实际做 Canny 边缘提取），因此“Canny 通道”在当前版本里等同于传入图像本身。这是后续可优化点。
> 见 pipeline_deep_dive.md 的说明

---

## 3. 参数说明（作用 + 调整建议）

- 调参前请固定好一个种子

- `prompt`
  - 作用：控制正向语义与风格方向
  - 建议：风格词、构图词、质量词分层组织

- `negative_prompt`
  - 作用：抑制低质特征与不希望出现的内容
  - 备注：后端会强制拼接 NSFW 防护前缀(虽然不知道有没有什么用;w;)

- `scribble_scale_stage1`
  - 作用：Stage1 中 Scribble 约束强度
  - 影响：越大越贴线稿，越小越放飞

- `canny_scale_stage1`
  - 作用：Stage1 中 Canny 约束强度
  - 备注：越大越贴线稿轮廓，越小越放飞

- `scribble_scale_stage2`
  - 作用：Stage2 精修时对结构的继续约束
  - 影响：过低会漂移，过高会“死板”

- `lcm_steps`
  - 增大：预览更稳但更慢, 而且LCM效果可能不太好, 太大了影响最终结果

- `lcm_guidance_scale`
  - Stage1 文本引导强度，过高易僵硬

- `lcm_denoise`
  - Stage1 去噪强度

- `latent_scale_factor`）
  - latent 放大倍率，影响最终分辨率与耗时

- `dpmpp_steps`
  - Stage2 迭代步数，越大通常质量越好但更慢

- `dpmpp_guidance_scale`
  - Stage2 文本引导强度，过高易出现过拟合感

- `dpmpp_denoise`
  - Stage2 重绘强度

## 建议谨慎改动

- `width` / `height`
  - 建议保持 8 的倍数；分辨率增大显著增加显存与耗时

- `output_format`
  - 默认 `png`，若改 `jpg/jpeg` 会有有损压缩

- `seed`
  - 用于复现。调优时可固定 seed 对比，出图时可随机

## 3.4 普通模式预设（由后端下发）

后端在 `/status` 返回 `basic_mode.presets`，前端动态渲染，不再写死。

默认包含：`Noob` / `Normal` / `Hardcore` / `God`。

---

## 4. 后端说明（server 侧）

## 4.1 技术栈与入口

- 框架：Flask
- 入口文件：`server.py`
- 模型构建：`src/pipeline.py`

## 4.2 主要接口

- `GET /`
  - 返回 `web/index.html`

- `GET /status`
  - 返回服务状态、设备、默认参数、普通模式预设
  - 返回 `busy`、`current_task`（空闲时为 `null`）、`progress`

- `POST /preview`
  - 仅跑 Stage1，用于前端自动预览
  - 服务忙时返回 HTTP 429（结构化 JSON，见 4.3）

- `POST /generate`
  - 跑完整 Stage1 + Stage2，返回最终图
  - 服务忙时返回 HTTP 429（结构化 JSON，见 4.3）

- `POST /switch_device`
  - 在 CPU / CUDA 之间切换推理设备
  - 推理或切换进行中时非阻塞返回 429（与 preview/generate 一致）

- `GET /outputs/<filename>`
  - 读取输出目录中的图片

## 4.3 当前后端关键机制

- 单飞行锁：同一时刻只允许一个占锁任务（preview / generate / switch_device），避免并发爆显存
- 服务忙时：preview / generate / switch_device 均使用非阻塞抢锁，失败返回 HTTP 429
- 429 响应：保留 `error` 字符串，并附带 `code`、`busy`、`retry_after_seconds`、`current_task`；响应头 `Retry-After`
- 任务状态：`GET /status` 返回 `current_task`（`task_id`、`type`、`started_at`、`elapsed_seconds`），空闲时为 `null`
- generate 与 preview 均在持锁后解析上传（忙时不做无效 body 解析）
- 参数解析：统一通过 `_parse_generation_params`
- 安全前缀：`negative_prompt` 会强制追加 NSFW 前缀
- NSFW 拦截：若 Stage1/Stage2 任一标记为 NSFW，返回 warning 并阻断图片下发

---

## 5. 前端说明（web 侧）

## 5.1 技术与入口

- 技术：原生 HTML/CSS/JavaScript
- 文件：`web/index.html`

## 5.2 已实现能力

- 画布编辑：画笔 / 橡皮擦 / 撤销 / 清空 / 上传 / 下载
- 自动预览：参数或画布变化后防抖触发 `/preview`
- 空画布跳过预览：避免无意义 GPU 请求
- 参数模式：普通 / 高级
- 页面初始化：从 `/status` 拉取默认参数和普通模式预设

## 5.3 与后端协作方式

- 发送：`multipart/form-data`
  - `image`: PNG Blob
  - `params`: JSON 字符串
- 展示：使用后端返回的 `preview_urls`

---

## 6. 项目结构与文件职责

以下是与“当前主流程”相关的核心文件：

- `server.py`
  - Web 服务入口、模型初始化、API 路由、参数解析、输出保存

- `web/index.html`
  - 页面 UI + 绘图逻辑 + 请求逻辑 + 参数模式切换

- `main.py`
  - 离线批处理入口（读取 `input/`，输出到 `output/`）

- `src/config.py`
  - 命令行参数定义

- `src/pipeline.py`
  - 构建 Stage1/Stage2 Diffusers pipeline

- `src/image_utils.py`
  - 图像预处理、输入文件扫描（含可改进的 Canny 预处理）

- `src/latent_utils.py`
  - latent 放大工具函数

- `requirements.txt`
  - Python 依赖清单

- `doc/web_ui.md`
  - Web UI 使用说明（补充文档）

---

## 7. 如何运行项目（给新同学）

## 7.1 环境要求（建议）

- Python 3.13(其实低一些版本可能更好, 有xformers可以用)
- NVIDIA GPU + CUDA（可选但强烈建议）
- Windows/Linux 均可（当前开发主要在 Windows）(N0a5shio: 我没测Linux, 有大手子可以测一下😋)

## 7.2 安装依赖

```text
pip install -r requirements.txt
```

当前 `requirements.txt` 已加入版本区间约束，区间基于当前可运行环境验证。

本地验证到的关键版本（供排查环境问题时参考）：

- `torch==2.6.0+cu124`
- `torchvision==0.21.0+cu124`
- `torchaudio==2.6.0+cu124`
- `diffusers==0.37.1`
- `transformers==5.5.0`
- `accelerate==1.13.0`
- `Pillow==12.1.1`
- `safetensors==0.7.0`
- `Flask==3.1.3`

> 注意：`+cu124` 是当前机器的 CUDA 轮子标签；在其他机器上可能是 CPU 版或不同 CUDA 版本，只要满足主版本区间通常可运行。

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

## 7.4 启动 Web 服务

```text
python server.py
```

默认地址：`http://127.0.0.1:5000/`

## 7.5 启动离线批处理（可选）

```text
python main.py --input_dir ./input --output_dir ./output
```

---

## 8. 建议的协作分工落地（技术视角）

- 见另一个文档

---

## 9. 已知问题与后续建议

- 前面说过了

---

## 10. 版本交接说明

本交接文档反映的是当前仓库可运行原型状态，目标是：

- 让不熟悉 SD 的同学能理解流程
- 让前后端同学知道从哪里改
- 让调优同学知道哪些参数最值得试

---

## 11. 调优与 LoRA 深入文档入口

如果你主要负责模型调优、Prompt 工程、LoRA 集成，请继续阅读：

- `doc/pipeline_deep_dive.md`

辛苦了

## 12. 有问题随时问(或者问AI可能更快)
