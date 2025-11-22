# 导入必要的模块
from DrissionPage import ChromiumPage
import json
import time
import random
import os
import re

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

# 工具函数
def _get_item_container(page, question_num):
    # 优先根据题号查找 index 节点，再取最近的 item 容器
    for _ in range(35):
        idx_ele = page.ele(
            f'xpath://div[contains(@class, "index") and normalize-space(.)="{question_num}."]'
        ) or page.ele(
            f'xpath://div[contains(@class, "index") and contains(normalize-space(.), "{question_num}")]'
        )
        if idx_ele:
            item = idx_ele.ele('xpath:ancestor::div[contains(@class, "item")][1]')
            if item:
                return item
        try:
            page.run_js('window.scrollBy(0, arguments[0]);', 700)
        except Exception:
            pass
        time.sleep(0.15)
    # 回退：直接按已渲染的 item 顺序取
    items = page.eles('xpath://div[contains(@class,"item")]')
    if not items:
        return None
    idx = max(0, question_num - 1)
    if idx >= len(items):
        return items[-1]
    return items[idx]

def _robust_click(page, target):
    try:
        target.click()
        return True
    except Exception:
        pass
    try:
        page.run_js('arguments[0].click();', target)
        return True
    except Exception:
        pass
    try:
        inner = target.ele('xpath:.//*[contains(@class,"inner")]')
        if inner:
            inner.click()
            return True
    except Exception:
        pass
    return False

def _scroll_to_item(page, question_num):
    container = _get_item_container(page, question_num)
    if not container:
        return None
    try:
        page.run_js('arguments[0].scrollIntoView({behavior:"auto", block:"center"});', container)
    except Exception:
        pass
    try:
        page.scroll.to_see(container)
    except Exception:
        pass
    time.sleep(0.2)
    return container

def _parse_hms_to_seconds(text):
    m = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', text or '')
    if not m:
        return None
    h, mi, s = map(int, m.groups())
    return h * 3600 + mi * 60 + s

def _fmt_seconds(sec):
    h = sec // 3600
    mi = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{mi:02d}:{s:02d}"

def _extract_letter(text):
    if not text:
        return None
    m = re.search(r'[A-Z]', str(text))
    if m:
        return m.group(0)
    m = re.search(r'[a-z]', str(text))
    if m:
        return m.group(0).upper()
    return None

def wait_until_submit_allowed(page, threshold_hms='01:40:00'):
    print("\n开始等待可交卷时间...")
    threshold_sec = _parse_hms_to_seconds(threshold_hms) or 6000
    last_log = -1
    while True:
        time_ele = page.ele('xpath://div[contains(@class, "time")]//span')
        if not time_ele:
            spans = page.eles('xpath://span')
            t_text = ''
            for sp in spans:
                ts = sp.text
                if _parse_hms_to_seconds(ts or '') is not None:
                    t_text = ts
                    break
            remaining = _parse_hms_to_seconds(t_text)
        else:
            remaining = _parse_hms_to_seconds(time_ele.text)

        if remaining is None:
            print("未读取到剩余时间，5秒后重试...")
            time.sleep(5)
            continue

        if remaining <= threshold_sec:
            print(f"已达到可交卷阈值 {threshold_hms}，当前剩余 { _fmt_seconds(remaining) }")
            break

        wait_left = remaining - threshold_sec
        if wait_left != last_log:
            print(f"距离可交卷还需: { _fmt_seconds(wait_left) } (当前剩余 { _fmt_seconds(remaining) })")
            last_log = wait_left
        sleep_for = min(30, max(5, wait_left // 10))
        time.sleep(sleep_for)

    submit = page.ele('xpath://div[contains(@class, "jiaoj")]//*[contains(text(), "交卷")]')
    if not submit:
        submit = page.ele('xpath://*[contains(text(), "交卷")]')
    if submit:
        try:
            page.scroll.to_see(submit)
        except Exception:
            pass
        clicked = _robust_click(page, submit)
        if clicked:
            print("已点击交卷按钮，尝试确认...")
            time.sleep(0.5)
            confirm = page.ele('xpath://button[contains(., "确定") or contains(., "确认")]')
            if confirm:
                _robust_click(page, confirm)
                print("已确认交卷")
            else:
                print("未检测到确认按钮，交卷可能已直接提交")
        else:
            print("交卷按钮点击失败")
    else:
        print("未找到交卷按钮")

def _is_radio_checked(ele):
    cls = ele.attr('class') or ''
    if 'ivu-radio-wrapper-checked' in cls:
        return True
    aria = ele.attr('aria-checked')
    return str(aria).lower() == 'true'

def _is_checkbox_checked(ele):
    cls = ele.attr('class') or ''
    if 'ivu-checkbox-wrapper-checked' in cls:
        return True
    aria = ele.attr('aria-checked')
    return str(aria).lower() == 'true'

def review_and_correct_answers(page, answers):
    print("\n开始校验并纠正答案...")
    fixed_j = 0
    fixed_s = 0
    fixed_m = 0

    for q in answers.get('判断题', []):
        num = q['题号']
        ans = str(q['答案']).strip()
        try:
            container = _scroll_to_item(page, num)
            if not container:
                continue
            radios = container.eles('xpath:.//label[contains(@class, "ivu-radio-wrapper")]')
            if not radios:
                continue
            sel_idx = None
            for i, r in enumerate(radios):
                if _is_radio_checked(r):
                    sel_idx = i
                    break
            exp_idx = 0 if ans in ["正确", "对", "True", "T", "是"] else 1
            if sel_idx is None or sel_idx != exp_idx:
                target = radios[exp_idx]
                inner = target.ele('.ivu-radio-inner') or target
                page.scroll.to_see(target)
                if _robust_click(page, inner) or _robust_click(page, target):
                    fixed_j += 1
                    print(f"第{num}题: 已纠正为{ans}")
                time.sleep(0.3)
        except Exception:
            pass

    for q in answers.get('单选题', []):
        num = q['题号']
        ans = _extract_letter(str(q['答案'])) or 'A'
        try:
            container = _scroll_to_item(page, num)
            if not container:
                continue
            opts = container.eles('xpath:.//label[contains(@class, "ivu-radio-wrapper")]')
            if not opts:
                continue
            sel_idx = None
            for i, o in enumerate(opts):
                if _is_radio_checked(o):
                    sel_idx = i
                    break
            exp = None
            for i, o in enumerate(opts):
                t = (o.text or '').strip()
                if t.startswith(f"{ans}.") or t.startswith(f"{ans}、") or t.startswith(f"{ans} "):
                    exp = i
                    break
            if exp is None:
                idx = ord(ans) - ord('A')
                exp = idx if 0 <= idx < len(opts) else 0
            if sel_idx is None or sel_idx != exp:
                target = opts[exp]
                inner = target.ele('.ivu-radio-inner') or target
                page.scroll.to_see(target)
                if _robust_click(page, inner) or _robust_click(page, target):
                    fixed_s += 1
                    print(f"第{num}题: 已纠正为{ans}")
                time.sleep(0.3)
        except Exception:
            pass

    for q in answers.get('多选题', []):
        num = q['题号']
        letters = [c for c in str(q['答案']).upper() if c.isalpha()]
        try:
            container = _scroll_to_item(page, num)
            if not container:
                continue
            opts = container.eles('xpath:.//label[contains(@class, "ivu-checkbox-wrapper")]')
            if not opts:
                continue
            changed = 0
            for ch in letters:
                exp = None
                for i, o in enumerate(opts):
                    t = (o.text or '').strip()
                    if t.startswith(f"{ch}.") or t.startswith(f"{ch}、") or t.startswith(f"{ch} "):
                        exp = i
                        break
                if exp is None:
                    idx = ord(ch) - ord('A')
                    exp = idx if 0 <= idx < len(opts) else None
                if exp is None:
                    continue
                o = opts[exp]
                if not _is_checkbox_checked(o):
                    inner = o.ele('.ivu-checkbox-inner') or o
                    page.scroll.to_see(o)
                    if _robust_click(page, inner) or _robust_click(page, o):
                        changed += 1
                        print(f"第{num}题: 勾选缺失选项{ch}")
                    time.sleep(0.2)
            if changed:
                fixed_m += 1
        except Exception:
            pass

    print(f"\n校验完成：纠正判断题{fixed_j}题，单选题{fixed_s}题，多选题{fixed_m}题")


# 填写判断题
def fill_judgment_questions(page, answers):
    """
    填写判断题答案
    判断题使用radio按钮，根据答案"正确"或"错误"点击对应的选项
    """
    success_count = 0
    fail_count = 0
    
    print("\n开始填写判断题...")
    
    for question in answers['判断题']:
        question_num = question['题号']
        answer = question['答案']
        
        try:
            container = _scroll_to_item(page, question_num)
            if not container:
                print(f"第{question_num}题: 未找到题目容器")
                fail_count += 1
                continue

            radios = container.eles('xpath:.//label[contains(@class, "ivu-radio-wrapper")]')
            if not radios or len(radios) < 2:
                # 兜底：在容器内找 radio 可视按钮
                radios = container.eles('xpath:.//span[contains(@class, "ivu-radio")]')
            if not radios or len(radios) < 2:
                print(f"第{question_num}题: 未找到选项按钮")
                fail_count += 1
                continue

            norm = str(answer).strip()
            if norm in ["正确", "对", "True", "T", "是"]:
                index = 0
            elif norm in ["错误", "错", "False", "F", "否"]:
                index = 1
            else:
                index = 0

            match_target = None
            for r in radios:
                txt = (r.text or '').strip()
                if index == 0 and ('对' in txt or '正确' in txt):
                    match_target = r
                    break
                if index == 1 and ('错' in txt or '错误' in txt):
                    match_target = r
                    break
            target = match_target or radios[index]
            inner = target.ele('.ivu-radio-inner') or target

            page.scroll.to_see(target)
            clicked = _robust_click(page, inner)
            if not clicked:
                clicked = _robust_click(page, target)
            if not clicked:
                print(f"第{question_num}题: 点击失败")
                fail_count += 1
                continue
            print(f"第{question_num}题: 成功点击{norm}选项")
            success_count += 1

            time.sleep(random.uniform(0.5, 1.2))

        except Exception as e:
            print(f"第{question_num}题: 填写失败 - {e}")
            fail_count += 1
    
    print(f"\n判断题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 填写单选题
def fill_single_choice_questions(page, answers):
    """
    填写单选题答案
    单选题使用radio按钮，根据答案字母(A、B、C等)点击对应的选项
    """
    success_count = 0
    fail_count = 0
    
    print("\n开始填写单选题...")
    
    for question in answers['单选题']:
        question_num = question['题号']
        answer = question['答案']
        
        try:
            container = _scroll_to_item(page, question_num)
            if not container:
                print(f"第{question_num}题: 未找到题目容器")
                fail_count += 1
                continue

            options = container.eles('xpath:.//label[contains(@class, "ivu-radio-wrapper")]')
            if not options:
                options = container.eles('xpath:.//span[contains(@class, "ivu-radio")]')
            if not options:
                print(f"第{question_num}题: 未找到选项")
                fail_count += 1
                continue

            letter = _extract_letter(answer) or 'A'
            idx = ord(letter) - ord('A')
            if idx < 0 or idx >= len(options):
                idx = 0
            match_target = None
            for i, opt in enumerate(options):
                txt = (opt.text or '').strip()
                if txt.startswith(f"{letter}.") or txt.startswith(f"{letter}、") or txt.startswith(f"{letter} "):
                    match_target = opt
                    break
            target = match_target or options[idx]
            inner = target.ele('.ivu-radio-inner') or target

            page.scroll.to_see(target)
            clicked = _robust_click(page, inner)
            if not clicked:
                clicked = _robust_click(page, target)
            if not clicked:
                print(f"第{question_num}题: 点击失败")
                fail_count += 1
                continue
            print(f"第{question_num}题: 成功点击选项{letter}")
            success_count += 1

            time.sleep(random.uniform(0.5, 1.2))

        except Exception as e:
            print(f"第{question_num}题: 填写失败 - {e}")
            fail_count += 1
    
    print(f"\n单选题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 填写多选题
def fill_multiple_choice_questions(page, answers):
    """
    填写多选题答案
    多选题使用checkbox按钮，根据答案字母组合(如ABCDE)点击对应的多个选项
    """
    success_count = 0
    fail_count = 0
    
    print("\n开始填写多选题...")
    
    for question in answers['多选题']:
        question_num = question['题号']
        answer = question['答案'].upper()  # 转换为大写字母
        
        try:
            container = _scroll_to_item(page, question_num)
            if not container:
                print(f"第{question_num}题: 未找到题目容器")
                fail_count += 1
                continue

            options = container.eles('xpath:.//label[contains(@class, "ivu-checkbox-wrapper")]')
            if not options:
                options = container.eles('xpath:.//span[contains(@class, "ivu-checkbox")]')
            if not options:
                alt_q = question_num - 1 if question_num > 1 else question_num + 1
                alt_container = _get_item_container(page, alt_q)
                if alt_container:
                    options = alt_container.eles('xpath:.//label[contains(@class, "ivu-checkbox-wrapper")]') or alt_container.eles('xpath:.//span[contains(@class, "ivu-checkbox")]')
            if not options:
                print(f"第{question_num}题: 未找到选项")
                fail_count += 1
                continue

            letters = [c for c in answer if c.isalpha()]
            click_count = 0
            for ch in letters:
                idx = ord(ch) - ord('A')
                if idx < 0 or idx >= len(options):
                    continue
                match_target = None
                for i, opt in enumerate(options):
                    txt = (opt.text or '').strip()
                    if txt.startswith(f"{ch}.") or txt.startswith(f"{ch}、") or txt.startswith(f"{ch} "):
                        match_target = opt
                        break
                target = match_target or options[idx]
                inner = target.ele('.ivu-checkbox-inner') or target

                # 如果已勾选则跳过，避免二次点击取消
                if 'ivu-checkbox-wrapper-checked' in (target.attr('class') or ''):
                    click_count += 1
                    continue

                page.scroll.to_see(target)
                did_click = _robust_click(page, inner)
                if not did_click:
                    did_click = _robust_click(page, target)
                if not did_click:
                    print(f"第{question_num}题: 选项{ch}点击失败")
                    continue
                print(f"第{question_num}题: 成功点击选项{ch}")
                click_count += 1
                time.sleep(random.uniform(0.3, 0.8))

            selected_final = 0
            for ch in letters:
                idx = ord(ch) - ord('A')
                if idx < 0 or idx >= len(options):
                    continue
                target = options[idx]
                if 'ivu-checkbox-wrapper-checked' in (target.attr('class') or ''):
                    selected_final += 1

            if selected_final >= 1:
                success_count += 1
                print(f"第{question_num}题: 已选中{selected_final}个目标选项")
            else:
                fail_count += 1

        except Exception as e:
            print(f"第{question_num}题: 填写失败 - {e}")
            fail_count += 1
    
    print(f"\n多选题填写完成:")
    print(f"- 成功: {success_count}题")
    print(f"- 失败: {fail_count}题")
    return success_count, fail_count

# 主函数
def main():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    answers_file = os.path.join(current_dir, 'exam_answers.json')
    
    # 加载答案
    answers = load_answers(answers_file)
    if not answers:
        print("无法继续，程序退出")
        return
    
    # 打开浏览器
    print("\n正在打开浏览器...")
    page = ChromiumPage()
    
    try:
        # 这里需要用户手动输入考试页面的URL
        # 或者可以修改为从配置文件读取
        exam_url = input("请输入考试页面的URL: ")
        
        # 打开考试页面
        print(f"正在打开考试页面: {exam_url}")
        page.get(exam_url)
        
        # 等待用户登录和页面加载完成
        input("\n请在浏览器中完成登录并进入考试页面，然后按Enter键继续...")
        
        # 填写各类题目答案
        print("\n开始自动填写答案...")
        
        # 填写判断题
        judgment_success, judgment_fail = fill_judgment_questions(page, answers)
        
        # 填写单选题
        single_success, single_fail = fill_single_choice_questions(page, answers)
        
        # 填写多选题
        multiple_success, multiple_fail = fill_multiple_choice_questions(page, answers)
        
        # 统计总结果
        total_success = judgment_success + single_success + multiple_success
        total_fail = judgment_fail + single_fail + multiple_fail
        total_questions = total_success + total_fail
        
        print("\n" + "="*50)
        print("答案填写完成！")
        print(f"总题数: {total_questions}")
        print(f"成功填写: {total_success}")
        print(f"填写失败: {total_fail}")
        print(f"成功率: {(total_success/total_questions*100):.1f}%")
        print("="*50)
        
        review_and_correct_answers(page, answers)
        print("\n启用定时交卷，阈值为剩余 01:40:00。")
        wait_until_submit_allowed(page, '01:40:00')
        print("\n请在浏览器中检查交卷状态。")
        input("按Enter键关闭浏览器并退出程序...")
        
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
    print("="*50)
    print("实验室安全考试答案自动填写工具")
    print("="*50)
    print("本工具将自动点击考试页面中的正确选项")
    print("支持判断题、单选题和多选题")
    print("="*50)
    main()
