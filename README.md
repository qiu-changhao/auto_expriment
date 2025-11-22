# 自动考试程序使用说明

## 功能概述
- 自动拉取试卷题目并生成结构化数据
- 调用大模型生成答案（支持环境变量或直接输入 API Key）
- 自动填写判断题、单选题、多选题，滚动到题目后点击可视按钮
- 在剩余时间小于等于 `01:40:00` 时自动点击“交卷”，并在等待过程中持续打印“距离可交卷还需”的时间

## 环境要求
- Python 3.8+
- 已安装依赖：
  - `pip install DrissionPage openai`
- 电脑可正常打开 Chromium/Chrome（DrissionPage 会自动驱动）

## 目录与主要脚本
- `auto_exam.py`：主程序，一键运行完整流程
- `get_question.py`：从考试页面监听接口并提取题目与选项
- `get_answers_from_model.py`：调用模型生成答案并输出为 `exam_answers.json`
- `fill_exam_answers.py`：自动滚动到题目并点击对应答案；支持定时交卷

## 快速开始
1. 准备 OpenAI API Key
   - 可将密钥放到环境变量（默认名：`DASHSCOPE_API_KEY`）或直接输入：
     - Windows CMD：`set DASHSCOPE_API_KEY=your_api_key`
     - PowerShell：`$env:DASHSCOPE_API_KEY='your_api_key'`
2. 运行主程序
   - `python auto_exam.py`
3. 按提示输入考试页面 URL
   - 例如：`https://sysaq.ustc.edu.cn/lab-study-front/routine-exam/5?examRequestId=XXXX`
4. 浏览器会打开考试页面，请登录并进入试卷
5. 程序自动：提题 → 获取答案 → 自动填写 → 等待到 `01:40:00` 阈值后交卷

## 交卷阈值说明
- 默认阈值为 `01:40:00`（剩余时间达到或低于该值时交卷）
- 如需修改：
  - 打开 `auto_exam.py`，将 `fill_exam_answers.wait_until_submit_allowed(page, '01:40:00')` 的参数改为需要的时间；例如 `'01:30:00'`

## 常见问题
- 无法读取剩余时间：确保页面上存在形如 `HH:MM:SS` 的时间文本；程序会优先读取 `div.time > span`，读不到将遍历页面 `span`
- 点击失败：程序会先滚动到题目容器，再点击 `label/inner` 可视控件，并提供 JS 点击回退；仍失败时，请确认页面类名是否与 iView 结构一致
- 多选题未找到：部分试卷多选题可能在第 `72` 或 `73` 题，程序已加入邻近题兜底；如仍异常，请提供该题的 DOM 结构以便完善选择器
- OpenAI API Key 未设置：主程序会提示输入环境变量名或直接输入 API Key；确保网络连通

## 温馨提示
- 登录后再继续自动流程，期间请不要关闭浏览器窗口
- 程序只负责自动点击考试页面中的可视按钮，不会修改服务器数据结构
- 请合理使用本工具，遵守考试规则与相关制度
