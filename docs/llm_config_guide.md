# LLM 配置教程

## 推荐方案

本项目推荐使用阿里云百炼的 OpenAI 兼容接口，因为当前代码已经按照 OpenAI-compatible Chat Completions 格式封装，只需要配置 API Key、Base URL 和模型名称即可。

推荐模型：

- `qwen3.7-plus`：推荐优先使用，适合简历解析、面试追问、评分反馈等综合任务。
- `qwen3.7-max`：更强，但通常成本更高，适合最终演示或关键报告生成。
- `qwen-plus`：稳定兜底，如果账号暂时没有 qwen3.7 系列权限，可以先用它。

## 配置步骤

### 1. 获取 API Key

进入阿里云百炼控制台，找到 API Key 管理页面，创建一个新的 API Key。

### 2. 创建 .env 文件

在项目根目录打开命令行，执行：

```bash
copy .env.example .env
```

### 3. 编辑 .env

用记事本或 VS Code 打开 `.env`，填写：

```text
LLM_API_KEY=你的真实APIKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-plus
USE_LLM=true
```

如果你在新加坡或使用国际账号，可以尝试：

```text
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

如果 `qwen3.7-plus` 不可用，改为：

```text
MODEL_NAME=qwen-plus
```

### 4. 重启项目

```bash
streamlit run app.py
```

### 5. 在页面中测试

打开“6. 项目说明与自检”页面，点击“测试 LLM 连接”。

成功后，页面会显示：

```text
LLM 连接测试成功
```

## 常见问题

### 左侧仍显示 LLM 未启用

检查 `.env` 中是否写了：

```text
USE_LLM=true
```

注意不要写成 `True` 也可以，但建议统一小写 `true`。

### 连接失败：401 / Unauthorized

通常是 API Key 错误、复制时多了空格，或者账号没有开通对应模型权限。

### 连接失败：404 / model not found

通常是模型名称不可用。把模型改成：

```text
MODEL_NAME=qwen-plus
```

再重启项目测试。

### 连接失败：timeout

可能是网络、地区 endpoint 或代理问题。可以尝试切换：

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
https://dashscope-intl.aliyuncs.com/compatible-mode/v1
https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1
```

## 安全提醒

不要把 `.env` 上传到 GitHub。项目中的 `.gitignore` 已经忽略 `.env`，但仍然不要手动上传真实 Key。
