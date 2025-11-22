import os
from DrissionPage import ChromiumPage
import get_question
import get_answers_from_model
import fill_exam_answers

def run(exam_url):
    print("开始自动考试")
    data = get_question.main(exam_url)
    if not data:
        print("获取题目失败")
        return
    get_answers_from_model.main()
    answers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exam_answers.json')
    answers = fill_exam_answers.load_answers(answers_path)
    if not answers:
        print("加载答案失败")
        return
    page = ChromiumPage()
    page.get(exam_url)
    print("开始填写答案")
    j_s, j_f = fill_exam_answers.fill_judgment_questions(page, answers)
    s_s, s_f = fill_exam_answers.fill_single_choice_questions(page, answers)
    m_s, m_f = fill_exam_answers.fill_multiple_choice_questions(page, answers)
    print("填写完成")
    total_s = j_s + s_s + m_s
    total_f = j_f + s_f + m_f
    total = total_s + total_f
    print(f"总题数: {total}")
    print(f"成功填写: {total_s}")
    print(f"填写失败: {total_f}")
    print("启动定时交卷")
    fill_exam_answers.wait_until_submit_allowed(page, '01:40:00')
    print("流程结束")

if __name__ == '__main__':
    url = input("请输入考试页面的URL: ")
    run(url)
