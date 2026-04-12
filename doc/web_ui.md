# Web UI 使用说明

## 入口

启动 `server.py` 后，浏览器访问：

- `http://127.0.0.1:5000/`

该页面提供：

- 400x600 草图画布（画笔 / 橡皮擦 / 撤销 / 清空 / 下载）
- 画布尺寸会跟随宽高设置动态变化
- 当画布尺寸较大时会显示性能警告
- 生成参数设置（Prompt、尺寸、Steps、Guidance 等）
- 参数/提示词/画布变更后，1 秒无继续改动时自动调用 `/preview` 生成 Stage1 预览
- 点击“生成”调用 `/generate`，执行完整 Stage1 + Stage2
- 显示 Stage1 预览、Canny、Final 输出

## 参数模式

- 普通模式：
	- 可编辑：`Prompt`、`Negative Prompt`、`宽度`、`高度`、`Seed`、`输出格式`、`ControlNet强度`
	- 自动使用预设覆盖三项参数：`scribble_scale_stage1`、`canny_scale_stage1`、`scribble_scale_stage2`

- 高级模式：
	- 保留全部参数可编辑（当前与服务端参数字段一一对应）

普通模式预设（S1 Scribble / S1 Canny / S2 Scribble）：

- `Noob`：`[0.6, 0.3, 0.5]`
- `Normal`：`[0.8, 0.5, 0.8]`
- `Hardcore`：`[1.1, 0.7, 1.1]`
- `God`：`[1.3, 0.9, 1.3]`

## 与后端接口

页面会调用以下接口：

- `GET /status`：查看服务状态（ready/busy/device）
- `POST /preview`：上传画布 PNG + 参数 JSON，仅执行 Stage1 并返回预览图
- `POST /generate`：上传画布 PNG + 参数 JSON
- `GET /outputs/<filename>`：加载输出图片用于预览

## 备注

- 默认画布是 `400x600`，和项目默认参数一致。
- 若服务返回 `429`，表示当前有任务在生成中，稍后重试。
- 页面结果区顺序为：Stage1 预览 → Final 输出 → Canny。
- 若修改了端口，请按实际端口访问。