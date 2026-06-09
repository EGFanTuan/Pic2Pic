# Web UI 使用说明

> 详细交接请优先阅读：`doc/project_handover.md`

## 入口

启动 `server.py` 后，浏览器访问：

- `http://127.0.0.1:5000/`

该页面提供：

- 400x600 草图画布（画笔 / 橡皮擦 / 撤销 / 清空 / 下载）
- 画布尺寸会跟随宽高设置动态变化
- 当画布尺寸较大时会显示性能警告
- 生成参数设置（Prompt、尺寸、Steps、Guidance 等）
- 参数/提示词/画布变更后，2 秒无继续改动时自动调用 `/preview` 生成 Stage1 预览
- 点击“生成”调用 `/generate`，执行完整 Stage1 + Stage2
- 显示 Stage1 预览、Canny、Final 输出
- 页面初始化会从后端 `GET /status` 拉取：
	- 默认参数（`defaults`）
	- 普通模式预设（`basic_mode.presets`）

## 参数模式

- 普通模式：
	- 可编辑：`Prompt`、`Negative Prompt`、`宽度`、`高度`、`Seed`、`输出格式`、`ControlNet强度`
	- 自动使用预设覆盖三项参数：`scribble_scale_stage1`、`canny_scale_stage1`、`scribble_scale_stage2`

- 高级模式：
	- 保留全部参数可编辑（当前与服务端参数字段一一对应）

普通模式预设（S1 Scribble / S1 Canny / S2 Scribble）：

- 由后端 `basic_mode.presets` 动态下发
- 默认预设由后端 `basic_mode.default_preset` 控制

## 与后端接口

页面会调用以下接口：

- `GET /status`：查看服务状态（ready/busy/device/current_task/progress）并拉取默认参数与普通模式预设
- `POST /preview`：上传画布 PNG + 参数 JSON，仅执行 Stage1 并返回预览图
- `POST /generate`：上传画布 PNG + 参数 JSON
- `POST /switch_device`：JSON `{ "device": "cpu" | "cuda" }` 切换推理设备
- `GET /outputs/<filename>`：加载输出图片用于预览

## 备注

- 默认画布是 `400x600`，和项目默认参数一致。
- 若服务返回 `429`，表示当前有占锁任务在执行（预览 / 完整生成 / 切换设备），请稍后重试。响应体示例：
  - `error`：中文说明（前端可直接展示）
  - `code`：`server_busy`
  - `retry_after_seconds`：建议重试间隔（秒）
  - `current_task`：当前占锁任务信息（`type` 为 `preview` / `generate` / `switch_device`）
  - 响应头 `Retry-After` 与 `retry_after_seconds` 一致
- `GET /status` 在空闲时 `current_task` 为 `null`；忙时与 429 中结构相同。
- 页面结果区顺序为：Stage1 预览 → Final 输出 → Canny。
- 若修改了端口，请按实际端口访问。
- 若画布为空，前端会跳过自动预览，避免无效推理请求。