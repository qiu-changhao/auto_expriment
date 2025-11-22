# 导入必要的库
import os
import json
from openai import OpenAI


def load_exam_data(file_path):
    """
    加载试卷数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
        print(f"成功加载试卷数据，包含以下题型：")
        for question_type, questions in exam_data.items():
            print(f"- {question_type}: {len(questions)}题")
        return exam_data
    except Exception as e:
        print(f"加载试卷数据失败: {e}")
        return None


def build_prompt(exam_data):
    """
    构建大模型提示词
    """
    prompt = "请为以下实验室安全考试题目提供正确答案。"\
             "\n\n请按照以下格式输出每道题的答案："\
             "\n- 第{题号}题：{答案}（答案只需要'正确'/'错误'或选项字母如'A'/'B'/'C'/'D'/'AB'/'AC'等）"\
             "\n\n"\
             "判断题（1-47题）：\n"
    
    # 添加判断题
    for question in exam_data['判断题']:
        prompt += f"第{question['题号']}题：{question['题目']}\n"
    
    prompt += "\n\n单选题（48-72题）：\n"
    
    # 添加单选题
    for question in exam_data['单选题']:
        prompt += f"第{question['题号']}题：{question['题目']}\n"
        options_text = "选项：\n"
        for opt in question['选项']:
            options_text += f"  [{opt['选项ID']}]: {opt['选项内容']}\n"
        prompt += options_text
    
    prompt += "\n\n多选题（73题）：\n"
    
    # 添加多选题
    for question in exam_data['多选题']:
        prompt += f"第{question['题号']}题：{question['题目']}\n"
        options_text = "选项：\n"
        for opt in question['选项']:
            options_text += f"  [{opt['选项ID']}]: {opt['选项内容']}\n"
        prompt += options_text
    
    prompt += "\n\n请为每道题提供准确的答案，注意多选题可能有多个正确选项。"
    return prompt


def call_model(prompt, api_key=None):
    """
    调用大模型获取答案
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        print("正在调用大模型获取答案...")
        completion = client.chat.completions.create(
            # 模型列表： `https://help.aliyun.com/zh/model-studio/getting-started/models`  
            model="qwen-plus",  
            messages=[
                {'role': 'system', 'content': '你是一名实验室安全专家，请为提供的实验室安全考试题目提供准确的答案。'},  
                {'role': 'user', 'content': prompt}
            ]
        )
        
        answer = completion.choices[0].message.content
        print("成功获取答案！")
        return answer
    except Exception as e:
        print(f"调用大模型失败: {e}")
        return None


def save_answers(answers, file_path):
    """
    保存答案到文件
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(answers)
        print(f"答案已保存到 {file_path}")
    except Exception as e:
        print(f"保存答案失败: {e}")


def parse_answers_to_json(model_answer, exam_data):
    """
    解析模型返回的答案为JSON格式
    """
    answers_dict = {
        "判断题": [],
        "单选题": [],
        "多选题": []
    }
    
    # 简单的解析逻辑，实际可能需要更复杂的处理
    lines = model_answer.split('\n')
    for line in lines:
        line = line.strip()
        # 处理带有'- '前缀的答案行
        if line.startswith("- "):
            line = line[2:].strip()
        if line.startswith("第") and "题：" in line:
            try:
                # 提取题号和答案
                parts = line.split("题：")
                if len(parts) != 2:
                    continue
                
                question_num = int(parts[0].replace("第", ""))
                answer = parts[1].strip()
                
                # 根据题号确定题型并添加答案
                if 1 <= question_num <= 47:
                    answers_dict["判断题"].append({
                        "题号": question_num,
                        "答案": answer
                    })
                elif 48 <= question_num <= 72:
                    answers_dict["单选题"].append({
                        "题号": question_num,
                        "答案": answer
                    })
                elif question_num == 73:
                    answers_dict["多选题"].append({
                        "题号": question_num,
                        "答案": answer
                    })
            except Exception as e:
                print(f"解析答案行失败 '{line}': {e}")
    
    return answers_dict


def save_answers_json(answers_dict, file_path):
    """
    保存JSON格式的答案
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(answers_dict, f, ensure_ascii=False, indent=2)
        print(f"JSON格式答案已保存到 {file_path}")
    except Exception as e:
        print(f"保存JSON格式答案失败: {e}")


def main():
    # 加载试卷数据
    exam_data = load_exam_data('extracted_exam_data.json')
    if not exam_data:
        return
    
    # 每次都调用大模型获取新答案，覆盖之前的答案
    print("调用大模型获取最新答案...")
    prompt = build_prompt(exam_data)
    api_key = resolve_api_key()
    if not api_key:
        return
    model_answer = call_model(prompt, api_key)
    if not model_answer:
        return
    
    # 保存原始答案，覆盖已有的文件
    print("覆盖保存最新获取的答案...")
    save_answers(model_answer, 'exam_answers.txt')
    
    # 解析并保存JSON格式答案，覆盖已有的文件
    answers_dict = parse_answers_to_json(model_answer, exam_data)
    save_answers_json(answers_dict, 'exam_answers.json')
    
    # 打印答案摘要
    print("\n答案提取摘要：")
    print(f"判断题答案数：{len(answers_dict['判断题'])}/47")
    print(f"单选题答案数：{len(answers_dict['单选题'])}/25")
    print(f"多选题答案数：{len(answers_dict['多选题'])}/1")
    print("\n最新答案已成功覆盖保存。")


if __name__ == "__main__":
    main()
def resolve_api_key(default_env_name='DASHSCOPE_API_KEY'):
    try:
        print("\n请输入存放 OpenAI API Key 的环境变量名，直接回车使用默认")
        print(f"默认环境变量名: {default_env_name}")
        env_name = input("环境变量名: ").strip() or default_env_name
        api_key = os.getenv(env_name)
        if not api_key:
            print("未从环境变量读取到 API Key，请直接输入 OpenAI API Key")
            api_key = input("OpenAI API Key: ").strip()
        if not api_key:
            print("未提供 API Key")
            return None
        return api_key
    except Exception:
        return None
