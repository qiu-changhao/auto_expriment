# 导入必要的模块
from DrissionPage import ChromiumPage
import json
import time
import random
import re
import os

# 定义目标交卷时间（1小时39分）
TARGET_TIME_MINUTES = 99  # 1小时39分 = 99分钟
TARGET_TIME_SECONDS = TARGET_TIME_MINUTES * 60

# 读取答案数据
def load_answers(answers_file):
    """
    从JSON文件加载答案数据
    """
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        print(f"成功加载答案数据，包含:")
        print(f"- 判断题: {len(answers['判断题'])}题")
        print(f"- 单选题: {len(answers['单选题'])}题")
        print(f"- 多选题: {len(answers['多选题'])}题")
        return answers
    except Exception as e:
        print(f"加载答案文件失败: {e}")
        return None

# 填写判断题
def fill_judgment_questions(page, answers, start_from=1):
    """
    填写判断题答案
    
    参数:
        page: 浏览器页面对象
        answers: 答案数据字典
        start_from: 从第几题开始填写（默认为1）
    """
    success_count = 0
    fail_count = 0
    
    print(f"\n开始填写判断题（从第{start_from}题开始）...")
    
    # 过滤出需要填写的题目
    questions_to_fill = [q for q in answers['判断题'] if q['题号'] >= start_from]
    
    if not questions_to_fill:
        print(f"没有需要填写的判断题（起始题号{start_from}超出范围）")
        return 0, 0
    
    for question in questions_to_fill:
        question_num = question['题号']
        answer = question['答案']
        
        try:
            # 查找当前题目的所有radio按钮
            radio_buttons = page.eles('.ivu-radio-input')
            
            if not radio_buttons:
                print(f"第{question_num}题: 未找到radio按钮")
                fail_count += 1
                continue
            
            target_button = None
            
            # 尝试通过选项文本查找
            try:
                if answer == "正确":
                    correct_label = page.ele(f'xpath://label[contains(text(), "正确")]/preceding-sibling::span/input[@class="ivu-radio-input"]')
                    if correct_label:
                        target_button = correct_label
                    else:
                        if len(radio_buttons) >= 1:
                            target_button = radio_buttons[0]
                else:
                    wrong_label = page.ele(f'xpath://label[contains(text(), "错误")]/preceding-sibling::span/input[@class="ivu-radio-input"]')
                    if wrong_label:
                        target_button = wrong_label
                    else:
                        if len(radio_buttons) >= 2:
                            target_button = radio_buttons[1]
            except:
                if answer == "正确" and len(radio_buttons) >= 1:
                    target_button = radio_buttons[0]
                elif answer == "错误" and len(radio_buttons) >= 2:
                    target_button = radio_buttons[1]
            
            if target_button:
                page.scroll.to_see(target_button)
                target_button.click()
                print(f"第{question_num}题: 成功点击{answer}选项")
                success_count += 1
            else:
                print(f"第{question_num}题: 未找到目标选项")
                fail_count += 1
            
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print(f"第{question_num}题: 填写失败 - {e}")
            fail_count += 1
    
    print(f"\n判断题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 填写单选题
def fill_single_choice_questions(page, answers, start_from=48):
    """
    填写单选题答案
    
    参数:
        page: 浏览器页面对象
        answers: 答案数据字典
        start_from: 从第几题开始填写（默认为48）
    """
    success_count = 0
    fail_count = 0
    
    print(f"\n开始填写单选题（从第{start_from}题开始）...")
    
    # 过滤出需要填写的题目
    questions_to_fill = [q for q in answers['单选题'] if q['题号'] >= start_from]
    
    if not questions_to_fill:
        print(f"没有需要填写的单选题（起始题号{start_from}超出范围）")
        return 0, 0
    
    for question in questions_to_fill:
        question_num = question['题号']
        answer = question['答案'].upper()
        radio_suffix = str(question_num - 1)
        
        try:
            print(f"\n处理第{question_num}题，答案: {answer}，radio_suffix: {radio_suffix}")
            
            # 方法1: 根据题号直接查找对应的radio按钮（优先方法）
            target_radio = None
            try:
                # 先找到所有radio按钮
                all_radios = page.eles('.ivu-radio-input')
                print(f"找到 {len(all_radios)} 个radio按钮")
                
                # 遍历查找name属性以特定后缀结尾的radio
                for radio in all_radios:
                    try:
                        name = radio.attr('name')
                        # 检查name属性是否以题号减一结尾
                        if name and name.endswith('_' + radio_suffix):
                            print(f"找到对应题号的radio按钮，name: {name}")
                            # 向上找到对应的选项wrapper
                            # 使用parent()方法替代ancestor
                            parent_elem = radio.parent()
                            wrapper = None
                            # 最多向上查找3层来找到wrapper
                            for _ in range(3):
                                if parent_elem:
                                    class_attr = parent_elem.attr('class') or ''
                                    if 'ivu-radio-wrapper' in class_attr:
                                        wrapper = parent_elem
                                        break
                                parent_elem = parent_elem.parent() if parent_elem else None
                            
                            if wrapper:
                                # 检查选项内容是否匹配答案
                                subject_title = wrapper.ele('.subject-title', timeout=0.5)
                                if subject_title:
                                    option_text = subject_title.text.strip()
                                    print(f"选项文本: {option_text}")
                                    if option_text.startswith(f"{answer}.") or option_text.startswith(f"{answer}、"):
                                        target_radio = radio
                                        print(f"找到匹配答案{answer}的radio按钮")
                                        break
                    except Exception as e:
                        print(f"检查radio时出错: {e}")
                        continue
            except Exception as e:
                print(f"方法1查找radio失败: {e}")
            
            # 方法2: 如果方法1失败，先找到题目区域，再在区域内查找选项
            if not target_radio:
                try:
                    # 查找题目区域
                    question_div = None
                    # 尝试通过id="item-{question_num}"查找题目区域
                    try:
                        question_div = page.ele(f'#item-{question_num}')
                        print(f"通过id找到第{question_num}题的题目区域")
                    except:
                        # 如果id查找失败，通过内容查找
                        all_items = page.eles('[class*="item-"]')
                        for item in all_items:
                            try:
                                index_elem = item.ele('.index')
                                if index_elem and index_elem.text.strip() == str(question_num):
                                    question_div = item
                                    print(f"通过index元素找到第{question_num}题的题目区域")
                                    break
                            except:
                                continue
                    
                    if question_div:
                        # 在题目区域内查找所有选项
                        option_wrappers = question_div.eles('.ivu-radio-wrapper')
                        print(f"在题目区域内找到 {len(option_wrappers)} 个选项")
                        
                        # 查找正确答案的选项
                        for wrapper in option_wrappers:
                            try:
                                subject_title = wrapper.ele('.subject-title', timeout=0.5)
                                if subject_title:
                                    option_text = subject_title.text.strip()
                                    print(f"检查选项: {option_text}")
                                    if option_text.startswith(f"{answer}.") or option_text.startswith(f"{answer}、"):
                                        # 找到对应的radio按钮
                                        radio = wrapper.ele('.ivu-radio-input')
                                        if radio:
                                            target_radio = radio
                                            print(f"在题目区域内找到匹配答案{answer}的radio按钮")
                                            break
                            except Exception as e:
                                print(f"检查选项时出错: {e}")
                                continue
                except Exception as e:
                    print(f"方法2查找失败: {e}")
            
            # 方法3: 全局搜索选项文本，然后找对应的radio按钮
            if not target_radio:
                try:
                    # 查找所有subject-title元素
                    all_subject_titles = page.eles('.subject-title')
                    print(f"找到 {len(all_subject_titles)} 个subject-title元素")
                    
                    for title in all_subject_titles:
                        try:
                            text = title.text.strip()
                            # 查找匹配答案的选项文本
                            if text.startswith(f"{answer}.") or text.startswith(f"{answer}、"):
                                # 向上找到radio-wrapper，使用parent()方法
                                parent_elem = title.parent()
                                wrapper = None
                                # 最多向上查找3层来找到wrapper
                                for _ in range(3):
                                    if parent_elem:
                                        class_attr = parent_elem.attr('class') or ''
                                        if 'ivu-radio-wrapper' in class_attr:
                                            wrapper = parent_elem
                                            break
                                    parent_elem = parent_elem.parent() if parent_elem else None
                                 
                                if wrapper:
                                    # 检查这个选项是否属于当前题目
                                    # 向上找到题目div
                                    current_question = wrapper.parent()
                                    for _ in range(3):
                                        if current_question:
                                            class_attr = current_question.attr('class') or ''
                                            if 'item-' in class_attr:
                                                break
                                        current_question = current_question.parent() if current_question else None
                                     
                                    if current_question:
                                        index_elem = current_question.ele('.index')
                                        if index_elem and index_elem.text.strip() == str(question_num):
                                            # 找到对应的radio按钮
                                            radio = wrapper.ele('.ivu-radio-input')
                                            if radio:
                                                target_radio = radio
                                                print(f"通过选项文本找到匹配答案{answer}的radio按钮")
                                                break
                        except Exception as e:
                            print(f"检查subject-title时出错: {e}")
                            continue
                except Exception as e:
                    print(f"方法3查找失败: {e}")
            
            # 如果找到目标radio按钮，执行点击
            if target_radio:
                # 确保元素可见
                page.scroll.to_see(target_radio)
                
                try:
                    # 直接点击radio按钮
                    target_radio.click()
                    print(f"第{question_num}题: 成功点击radio按钮，选项{answer}")
                    success_count += 1
                except Exception as e:
                    # 如果直接点击radio失败，尝试点击其父元素
                    try:
                        parent = target_radio.parent()
                        if parent:
                            parent.click()
                            print(f"第{question_num}题: 成功点击radio父元素")
                            success_count += 1
                        else:
                            print(f"第{question_num}题: 找不到radio父元素")
                            fail_count += 1
                    except Exception as e2:
                        print(f"第{question_num}题: 点击失败 - {e2}")
                        fail_count += 1
            else:
                print(f"第{question_num}题: 未找到匹配答案{answer}的radio按钮")
                fail_count += 1
            
            # 添加随机延时
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"第{question_num}题: 填写过程中出错 - {e}")
            fail_count += 1
            time.sleep(1)
    
    print(f"\n单选题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 填写多选题
def fill_multiple_choice_questions(page, answers, start_from=73):
    """
    填写多选题答案
    
    参数:
        page: 浏览器页面对象
        answers: 答案数据字典
        start_from: 从第几题开始填写（默认为73）
    """
    success_count = 0
    fail_count = 0
    
    print(f"\n开始填写多选题（从第{start_from}题开始）...")
    
    # 过滤出需要填写的题目
    questions_to_fill = [q for q in answers['多选题'] if q['题号'] >= start_from]
    
    if not questions_to_fill:
        print(f"没有需要填写的多选题（起始题号{start_from}超出范围）")
        return 0, 0
    
    for question in questions_to_fill:
        question_num = question['题号']
        answer = question['答案'].upper()
        
        try:
            option_wrappers = page.eles('.ivu-checkbox-wrapper')
            
            if not option_wrappers:
                print(f"第{question_num}题: 未找到选项")
                fail_count += 1
                continue
            
            clicked_options = 0
            
            for char in answer:
                target_option = None
                
                for wrapper in option_wrappers:
                    try:
                        option_text = wrapper.text.strip()
                        if option_text.startswith(f"{char}.") or option_text.startswith(f"{char}、"):
                            target_option = wrapper
                            break
                        
                        checkbox_input = wrapper.ele('.ivu-checkbox-input', timeout=0.5)
                        if checkbox_input:
                            value = checkbox_input.attr('value')
                            if value and (value == char or value.upper() == char):
                                target_option = wrapper
                                break
                    except:
                        continue
                
                if target_option:
                    page.scroll.to_see(target_option)
                    target_option.click()
                    print(f"第{question_num}题: 成功点击选项{char}")
                    clicked_options += 1
                    time.sleep(random.uniform(0.3, 0.8))
                else:
                    print(f"第{question_num}题: 未找到选项{char}")
            
            if clicked_options > 0:
                success_count += 1
                print(f"第{question_num}题: 成功点击{clicked_options}个选项")
            else:
                fail_count += 1
            
        except Exception as e:
            print(f"第{question_num}题: 填写失败 - {e}")
            fail_count += 1
    
    print(f"\n多选题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 解析时间字符串为秒数
def parse_time_string(time_str):
    """
    解析时间字符串为秒数
    """
    try:
        time_str = time_str.strip()
        time_parts = re.findall(r'\d+', time_str)
        
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(time_parts) == 2:
            minutes, seconds = map(int, time_parts)
            total_seconds = minutes * 60 + seconds
        else:
            raise ValueError(f"无法解析时间格式: {time_str}")
        
        return total_seconds
    except Exception as e:
        print(f"解析时间失败: {e}")
        return None

# 格式化秒数为时间字符串
def format_time(seconds):
    """
    将秒数格式化为 HH:MM:SS 格式
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds_remaining = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_remaining:02d}"

# 点击交卷按钮
def click_submit_button(page):
    """
    查找并点击交卷按钮
    """
    print("正在查找并点击交卷按钮...")
    submit_button_found = False
    
    # 方法1: 查找包含"交卷"文本的元素
    try:
        submit_elements = page.eles('contains:交卷')
        for element in submit_elements:
            if element.ele('.ivu-icon') or '交卷' in element.text:
                print("找到交卷按钮（方法1）")
                page.scroll.to_see(element)
                element.click()
                submit_button_found = True
                print("已点击交卷按钮")
                break
    except Exception as e:
        print(f"方法1查找交卷按钮失败: {e}")
    
    # 方法2: 查找具有指定图标的元素
    if not submit_button_found:
        try:
            icon_elements = page.eles('.ivu-icon-ios-checkmark')
            for icon in icon_elements:
                parent = icon.parent()
                if parent and '交卷' in parent.text:
                    print("找到交卷按钮（方法2）")
                    page.scroll.to_see(parent)
                    parent.click()
                    submit_button_found = True
                    print("已点击交卷按钮")
                    break
        except Exception as e:
            print(f"方法2查找交卷按钮失败: {e}")
    
    # 方法3: 查找所有button元素并检查
    if not submit_button_found:
        try:
            buttons = page.eles('tag:button')
            for button in buttons:
                if '交卷' in button.text:
                    print("找到交卷按钮（方法3）")
                    page.scroll.to_see(button)
                    button.click()
                    submit_button_found = True
                    print("已点击交卷按钮")
                    break
        except Exception as e:
            print(f"方法3查找交卷按钮失败: {e}")
    
    # 方法4: 查找具有特定数据属性的元素
    if not submit_button_found:
        try:
            jiaojuan_element = page.ele('data-v-37cf69d4.ivu-button')
            if jiaojuan_element and '交卷' in jiaojuan_element.text:
                print("找到交卷按钮（方法4）")
                page.scroll.to_see(jiaojuan_element)
                jiaojuan_element.click()
                submit_button_found = True
                print("已点击交卷按钮")
        except Exception as e:
            print(f"方法4查找交卷按钮失败: {e}")
    
    if submit_button_found:
        time.sleep(2)
        
        try:
            confirm_buttons = page.eles('contains:确认')
            for button in confirm_buttons:
                if button.visible and '确认' in button.text:
                    print("找到确认交卷按钮，点击确认")
                    button.click()
                    print("\n✓ 交卷操作完成！")
                    return True
        except Exception as e:
            print(f"点击确认按钮失败: {e}")
            print("请手动确认交卷")
            return True
    else:
        print("警告: 未找到交卷按钮，请手动交卷")
        return False

# 监控剩余时间并交卷
def monitor_and_submit(page):
    """
    监控剩余时间并在达到目标时间时点击交卷按钮
    """
    print(f"\n开始监控剩余时间，目标交卷时间: {format_time(TARGET_TIME_SECONDS)}")
    check_interval = 10
    
    while True:
        try:
            remaining_time = None
            
            # 方法1: 使用data属性选择器
            try:
                time_element = page.ele('data-v-37cf69d4')
                if time_element:
                    time_span = time_element.ele('tag:span')
                    if time_span:
                        remaining_time = time_span.text
                        print(f"找到时间元素，剩余时间: {remaining_time}")
            except:
                print("方法1查找时间元素失败")
            
            # 方法2: 使用类名查找
            if not remaining_time:
                try:
                    time_elements = page.eles('.time')
                    for element in time_elements:
                        time_text = element.text.strip()
                        if ':' in time_text:
                            remaining_time = time_text
                            print(f"方法2找到时间，剩余时间: {remaining_time}")
                            break
                except:
                    print("方法2查找时间元素失败")
            
            # 方法3: 查找所有包含时间格式的span元素
            if not remaining_time:
                try:
                    all_spans = page.eles('tag:span')
                    for span in all_spans:
                        span_text = span.text.strip()
                        if re.match(r'\d+:\d+(:\d+)?', span_text):
                            remaining_time = span_text
                            print(f"方法3找到时间，剩余时间: {remaining_time}")
                            break
                except:
                    print("方法3查找时间元素失败")
            
            if remaining_time:
                total_seconds = parse_time_string(remaining_time)
                if total_seconds is not None:
                    print(f"当前剩余时间: {format_time(total_seconds)}，目标时间: {format_time(TARGET_TIME_SECONDS)}")
                    
                    if total_seconds <= TARGET_TIME_SECONDS + 10:
                        print(f"\n✓ 达到目标交卷时间！剩余时间: {format_time(total_seconds)}")
                        return click_submit_button(page)
            else:
                print("未找到剩余时间元素，继续尝试...")
            
            print(f"继续监控，{check_interval}秒后再次检查...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            return False
        except Exception as e:
            print(f"监控过程中出错: {e}")
            time.sleep(5)

# 主函数
def main():
    print("="*60)
    print("实验室安全考试自动化工具 - 完整版")
    print("="*60)
    print("功能1: 自动填写考试答案（判断题、单选题、多选题）")
    print(f"功能2: 在剩余时间达到 {format_time(TARGET_TIME_SECONDS)} 时自动交卷")
    print("="*60)
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    answers_file = os.path.join(current_dir, 'exam_answers.json')
    
    # 加载答案
    print("\n正在加载答案数据...")
    answers = load_answers(answers_file)
    if not answers:
        print("无法加载答案数据，程序退出")
        return
    
    # 打开浏览器
    print("\n正在打开浏览器...")
    page = ChromiumPage()
    
    try:
        # 获取考试页面URL
        exam_url = input("请输入考试页面的URL: ")
        
        # 打开考试页面
        print(f"正在打开考试页面: {exam_url}")
        page.get(exam_url)
        
        # 等待用户登录和页面加载完成
        input("\n请在浏览器中完成登录并进入考试页面，然后按Enter键继续...")
        
        # 询问从哪一题开始填写
        default_start = 1
        while True:
            try:
                start_input = input(f"\n请输入开始填写的题号（默认为{default_start}，直接按Enter从第{default_start}题开始）: ").strip()
                start_from = int(start_input) if start_input else default_start
                if start_from < 1:
                    print("题号不能小于1，请重新输入")
                    continue
                break
            except ValueError:
                print("请输入有效的数字")
        
        # 填写各类题目答案
        print(f"\n开始自动填写答案（从第{start_from}题开始）...")
        
        # 根据起始题号确定各类题目的起始位置
        judgment_start = start_from if start_from <= 47 else 48  # 判断题范围1-47
        single_start = max(start_from, 48)  # 单选题范围48-72
        multiple_start = max(start_from, 73)  # 多选题范围73-
        
        # 填写判断题
        judgment_success, judgment_fail = fill_judgment_questions(page, answers, judgment_start)
        
        # 填写单选题
        single_success, single_fail = fill_single_choice_questions(page, answers, single_start)
        
        # 填写多选题
        multiple_success, multiple_fail = fill_multiple_choice_questions(page, answers, multiple_start)
        
        # 统计总结果
        total_success = judgment_success + single_success + multiple_success
        total_fail = judgment_fail + single_fail + multiple_fail
        total_questions = total_success + total_fail
        
        print("\n" + "="*60)
        print("答案填写完成！")
        print(f"总题数: {total_questions}")
        print(f"成功填写: {total_success}")
        print(f"填写失败: {total_fail}")
        print(f"成功率: {(total_success/total_questions*100):.1f}%")
        print("="*60)
        
        # 询问是否开始监控交卷
        monitor_choice = input("\n是否开始监控剩余时间并自动交卷？(y/n): ").strip().lower()
        
        if monitor_choice == 'y':
            print("\n开始监控考试剩余时间...")
            success = monitor_and_submit(page)
            
            if success:
                print("\n考试自动交卷任务已完成")
            else:
                print("\n考试自动交卷任务未完成，请检查")
        else:
            print("\n跳过自动交卷功能，请手动交卷")
        
        input("\n按Enter键关闭浏览器并退出程序...")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
    finally:
        # 关闭浏览器
        print("\n正在关闭浏览器...")
        page.close()
        print("程序已退出")

if __name__ == "__main__":
    main()
