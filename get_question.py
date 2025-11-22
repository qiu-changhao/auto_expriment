# 导入必要的库
from DrissionPage import ChromiumPage
from pprint import pprint
import json
import os


def extract_options(subject_items):
    """
    从subjectItems中提取选项
    处理可能的字典或列表结构
    """
    options = []
    if not subject_items:
        return options
    
    # 处理列表结构
    if isinstance(subject_items, list):
        for opt in subject_items:
            if isinstance(opt, dict):
                options.append({
                    '选项ID': opt.get('id', ''),
                    '选项内容': opt.get('content', '')
                })
    # 处理字典结构
    elif isinstance(subject_items, dict):
        for key, value in subject_items.items():
            # 处理嵌套字典
            if isinstance(value, dict):
                options.append({
                    '选项ID': value.get('id', ''),
                    '选项内容': value.get('content', '')
                })
            # 处理直接是选项列表的情况
            elif isinstance(value, list):
                for opt in value:
                    if isinstance(opt, dict):
                        options.append({
                            '选项ID': opt.get('id', ''),
                            '选项内容': opt.get('content', '')
                        })
    
    return options


def main():
    """
    主函数，用于提取试卷题目和选项
    """
    # 存储不同类型的题目
    exam_data = {
        '判断题': [],
        '单选题': [],
        '多选题': []
    }

    try:
        # 打开浏览器
        page = ChromiumPage()
        # 监听数据包
        page.listen.start('https://sysaq.ustc.edu.cn/cg-exam-server/api/exam_center/do_exam?examRequestId=767307a43b05497087af4c5669052cb9&examId=5&nocache')
        # 打开第一页
        page.get('https://sysaq.ustc.edu.cn/lab-study-front/routine-exam/5?examRequestId=7815e28c3b874f989cbe9dd1af0a5f4c')
        # 等待数据包加载完成
        rep = page.listen.wait()
        
        # 获取所有题目
        try:
            subjects = rep.response.body['data']['data']['paper']['subjects']
            if not isinstance(subjects, list):
                print("警告: 题目数据格式异常")
                return None
        except (KeyError, AttributeError) as e:
            print(f"错误: 无法获取题目数据 - {e}")
            return None

        # 提取判断题（1-47题）
        for i in range(47):
            if i < len(subjects):
                subject = subjects[i]
                question_info = {
                    '题号': i + 1,
                    '题目': subject.get('subjectContent', ''),
                    '类型': '判断题'
                }
                exam_data['判断题'].append(question_info)

        # 提取单选题（48-72题）
        for i in range(47, 72):
            if i < len(subjects):
                subject = subjects[i]
                # 提取题目内容
                question_content = subject.get('subjectContent', '')
                
                # 提取选项
                options = extract_options(subject.get('subjectItems', []))
                
                question_info = {
                    '题号': i + 1,
                    '题目': question_content,
                    '选项': options,
                    '类型': '单选题'
                }
                exam_data['单选题'].append(question_info)

        # 提取多选题（73题）
        i = 72  # 索引从0开始，第73题的索引是72
        if i < len(subjects):
            subject = subjects[i]
            # 提取题目内容
            question_content = subject.get('subjectContent', '')
            
            # 提取选项
            options = extract_options(subject.get('subjectItems', []))
            
            question_info = {
                '题号': i + 1,
                '题目': question_content,
                '选项': options,
                '类型': '多选题'
            }
            exam_data['多选题'].append(question_info)
        
        # 保存提取的数据到JSON文件，方便后续使用
        try:
            with open('extracted_exam_data.json', 'w', encoding='utf-8') as f:
                json.dump(exam_data, f, ensure_ascii=False, indent=2)
            print("\n题目数据已保存到 extracted_exam_data.json 文件")
        except Exception as e:
            print(f"警告: 无法保存数据到文件 - {e}")
            
        return exam_data
        
    except Exception as e:
        print(f"程序运行出错: {e}")
        return None


if __name__ == "__main__":
    # 执行主函数
    exam_data = main()
    
    if exam_data:
        # 打印提取的判断题
        print("=== 判断题（1-47题）===")
        for question in exam_data['判断题']:
            print(f"第{question['题号']}题: {question['题目']}")

        print(f"\n共提取到 {len(exam_data['判断题'])} 道判断题")

        # 打印提取的单选题
        print("\n=== 单选题（48-72题）===")
        for question in exam_data['单选题']:
            print(f"\n第{question['题号']}题: {question['题目']}")
            print("选项:")
            for opt in question['选项']:
                print(f"  [{opt['选项ID']}]: {opt['选项内容']}")

        print(f"\n共提取到 {len(exam_data['单选题'])} 道单选题")

        # 打印提取的多选题
        print("\n=== 多选题（73题）===")
        for question in exam_data['多选题']:
            print(f"\n第{question['题号']}题: {question['题目']}")
            print("选项:")
            for opt in question['选项']:
                print(f"  [{opt['选项ID']}]: {opt['选项内容']}")

        print(f"\n共提取到 {len(exam_data['多选题'])} 道多选题")

        # 打印总题数
        print(f"\n=== 试卷汇总 ===")
        print(f"判断题: {len(exam_data['判断题'])} 题")
        print(f"单选题: {len(exam_data['单选题'])} 题")
        print(f"多选题: {len(exam_data['多选题'])} 题")
        print(f"总题数: {len(exam_data['判断题']) + len(exam_data['单选题']) + len(exam_data['多选题'])} 题")


