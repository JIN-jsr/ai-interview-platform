# LLM 配置教程

## 1. 配置文件

项目通过 `.env` 读取本地 LLM 配置。首次使用时复制模板：

```bash
copy .env.example .env
```

然后在 `.env` 中填写：

```env
USE_LLM=true
LLM_API_KEY=your_real_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-plus
```

修改 `.env` 后需要重启 Streamlit。

## 2. 无密钥或备用模式

如果没有 API Key，或需要演示本地规则 fallback：

```env
USE_LLM=false
```

此时系统仍可完成简历解析 fallback、规则出题、回答分析和评分报告生成。

## 3. Base URL 与模型

常见 OpenAI-compatible endpoint：

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
https://dashscope-intl.aliyuncs.com/compatible-mode/v1
https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1
```

模型是否可用取决于账号权限、服务地域和开通状态。不要假设所有账号都能使用同一个模型。如果 `qwen3.7-plus` 不可用，可根据账号权限更换为其他兼容模型。

## 4. 页面测试

启动项目后，可在“项目说明与运行检查”页面点击“测试 LLM 连接”。成功时页面会显示连接成功；失败时系统仍会保留本地 fallback。

## 5. 常见错误

### 401 / Unauthorized

可能原因：

- API Key 错误。
- 复制时多了空格。
- Key 已失效或权限不足。

处理方式：重新复制 API Key，确认 `.env` 未写入引号或多余空格。

### 404 / model not found

可能原因：

- 模型名称不存在。
- 当前账号或地域没有该模型权限。

处理方式：检查模型名称，或切换到账号已开通的模型。

### timeout

可能原因：

- 本地网络到服务端点不稳定。
- 地区 endpoint 不匹配。
- 代理只作用于浏览器，没有作用于 Python 请求。

处理方式：切换网络、检查代理设置、尝试不同 Base URL。系统会在超时后自动使用本地规则。

### 429 / rate limit

可能原因：

- 调用频率过高。
- 账号额度或并发限制。

处理方式：稍后重试，降低频率，或检查账号额度。

## 6. 安全要求

- 不要提交 `.env`。
- 不要把真实 API Key 写入 README、设计文档、截图或提交记录。
- `.env.example` 只能包含占位值。
- 录制视频前检查页面和终端，避免暴露 Key。
