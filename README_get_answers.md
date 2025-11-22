# 实验室安全考试答案获取工具

本工具用于调用阿里云通义千问大模型，为实验室安全考试题目自动生成答案。

## 功能特点

- 读取已提取的试卷数据（`extracted_exam_data.json`）
- 构建结构化提示词，包含所有判断题、单选题和多选题
- 调用阿里云通义千问大模型（qwen-plus）获取答案
- 保存原始答案文本和结构化JSON格式答案
- 提供答案提取摘要统计

## 使用步骤

### 1. 准备工作

- 确保已成功提取试卷数据到 `extracted_exam_data.json` 文件
- 申请阿里云百炼模型服务的 API Key
  - 申请地址：[https://help.aliyun.com/zh/model-studio/get-api-key](https://help.aliyun.com/zh/model-studio/get-api-key)

### 2. 设置 API Key

在运行脚本前，需要设置环境变量 `DASHSCOPE_API_KEY`：

**Windows 命令行：**
```cmd
set DASHSCOPE_API_KEY=your_api_key_here
```

**PowerShell：**
```powershell
$env:DASHSCOPE_API_KEY='your_api_key_here'
```

**或者直接在代码中设置（不推荐，出于安全考虑）：**
修改 `get_answers_from_model.py` 文件中的 `api_key` 参数：
```python
api_key="your_api_key_here"
```

### 3. 运行脚本

```powershell
python get_answers_from_model.py
```

### 4. 查看结果

脚本运行完成后，会生成两个文件：

- `exam_answers.txt` - 大模型返回的原始答案文本
- `exam_answers.json` - 结构化的JSON格式答案

## 输出格式说明

### JSON格式答案示例

```json
{
  "判断题": [
    {"题号": 1, "答案": "正确"},
    {"题号": 2, "答案": "正确"}
  ],
  "单选题": [
    {"题号": 48, "答案": "A"},
    {"题号": 49, "答案": "B"}
  ],
  "多选题": [
    {"题号": 73, "答案": "ABCD"}
  ]
}
```

## 注意事项

1. **API Key 安全**：请妥善保管您的 API Key，避免泄露
2. **地域选择**：根据您的 API Key 所属地域，可能需要修改 `base_url`：
   - 北京地域：`https://dashscope.aliyuncs.com/compatible-mode/v1`
   - 新加坡地域：`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
3. **模型选择**：默认使用 `qwen-plus`，您可以根据需要修改为其他模型
4. **答案准确性**：大模型生成的答案仅供参考，请仔细核对
5. **费用说明**：调用阿里云百炼模型服务可能产生费用，请查看官方计费说明

## 常见问题

### Q: 运行脚本时提示缺少 openai 库怎么办？
A: 请先安装 openai 库：
```powershell
pip install openai
```

### Q: 如何修改调用的模型？
A: 修改 `get_answers_from_model.py` 文件中的 `model` 参数，例如改为 `qwen-max`

### Q: 答案解析不正确怎么办？
A: 可能需要调整 `parse_answers_to_json` 函数中的解析逻辑，以适应不同的输出格式

## 模型信息

- 官方文档：[https://help.aliyun.com/zh/model-studio/getting-started/models](https://help.aliyun.com/zh/model-studio/getting-started/models)
- 模型列表：qwen-plus, qwen-max, qwen3-max 等

## 免责声明

本工具仅供学习和参考使用，请勿用于任何违反考试规则或学术诚信的行为。使用本工具产生的一切后果由使用者自行承担。