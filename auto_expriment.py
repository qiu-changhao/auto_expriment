# 导入必要的模块
from DrissionPage import ChromiumPage
from pprint import pprint
import random
import time
import os
import sys

# 定义一个函数，将秒数转换为分:秒格式
def format_time(seconds):
    minutes = int(seconds // 60)
    seconds_remaining = int(seconds % 60)
    return f"{minutes}:{seconds_remaining:02d}"

# 定义一个函数，将时间字符串（支持时:分:秒和分:秒格式）转换为秒数
def time_str_to_seconds(time_str):
    # 移除可能的空格
    time_str = time_str.strip()
    # 分割时间部分
    parts = time_str.split(':')
    # 处理不同格式
    if len(parts) == 3:  # 时:分:秒格式
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:  # 分:秒格式
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"无效的时间格式: {time_str}")

# 必学时长（秒）
REQUIRED_TOTAL_HOURS = 4
REQUIRED_TOTAL_SECONDS = REQUIRED_TOTAL_HOURS * 3600

# 从name_list.txt读取内容到name_list列表
name_list = []
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'name_list.txt')
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        name_list = [line.strip() for line in f.readlines()]
    print(f"成功从{file_path}读取{len(name_list)}行内容到name_list")
else:
    print(f"警告：未找到{file_path}文件")

# 打开浏览器
page = ChromiumPage()
# 打开第一页
page.get('https://sysaq.ustc.edu.cn/lab-study-front/examTask/5/4/1/42')
 # 添加随机延时，避免被反爬
sleep_time = random.uniform(250, 280)
 # 记录开始时间
start_time = time.time()
# 页面停留计时器（秒）
page_stay_time = 0
# 页面刷新阈值（秒） - 设置为4分45秒，比5分钟提前15秒刷新
REFRESH_THRESHOLD = 285  # 4*60 + 45 = 285秒

# 点击下一页并继续爬取
for i, text in enumerate(name_list):
    # 记录当前循环开始时间
    loop_start_time = time.time()
    
    # 检查已学时长是否达到必学时长
    try:
        # 获取已学时长元素
        study_time_ele = page.ele('.text-1')
        if study_time_ele:
            current_study_time = study_time_ele.text
            study_time_seconds = time_str_to_seconds(current_study_time)
            
            # 显示当前学习进度
            progress_percentage = (study_time_seconds / REQUIRED_TOTAL_SECONDS) * 100
            print(f"当前已学习时间: {current_study_time}，进度: {progress_percentage:.1f}%")
            
            # 检查是否达到必学时长
            if study_time_seconds >= REQUIRED_TOTAL_SECONDS:
                print(f"恭喜！已完成{REQUIRED_TOTAL_HOURS}小时的必学时长要求。")
                print(f"最终学习时间: {current_study_time}")
                # 关闭浏览器
                page.close()
                # 退出程序
                sys.exit(0)
    except Exception as study_time_e:
        print(f"获取已学时长信息时出错: {str(study_time_e)}")
    
    try:
        # 首先检查页面是否存在该name
        # 使用类选择器定位元素，然后筛选包含目标文本的元素
        item_elements = page.eles('.itemTitle')
        next_page_selector = None
        
        # 检查所有itemTitle元素中是否包含当前text
        name_exists = False
        for element in item_elements:
            if text in element.text:
                name_exists = True
                next_page_selector = element
                break
        
        # 如果在.itemTitle中没找到，尝试在整个页面中搜索
        if not name_exists:
            try:
                # 尝试使用contains选择器在整个页面中查找
                page.ele(f'contains({text})')
                name_exists = True
            except:
                # 如果抛出异常，说明不存在该文本
                name_exists = False
        
        # 如果页面中不存在该name，直接跳过进行下一个
        if not name_exists:
            print(f"页面中不存在 '{text}'，直接进行下一个")
            continue
        
        # 只有找到元素后才执行操作
        if next_page_selector:
            page.scroll.to_see(next_page_selector)
            # 点击下一页按钮
            next_page_selector.click()     
            print(f"成功点击: {text}")
            
            # 尝试获取学习时间信息
            try:
                # 获取要求学习时间
                all_time_ele = page.ele('.allTime')
                # 获取已学习时间
                already_time_ele = page.ele('.alredyTime')
                
                if all_time_ele and already_time_ele:
                    # 转换时间
                    all_time_seconds = time_str_to_seconds(all_time_ele.text)
                    already_time_seconds = time_str_to_seconds(already_time_ele.text)
                    
                    # 计算需要的额外学习时间（秒）
                    required_sleep_time = max(0, all_time_seconds - already_time_seconds)
                    print(f"要求学习时间: {all_time_ele.text}, 已学习时间: {already_time_ele.text}, 需要额外学习时间: {required_sleep_time} 秒")
                    
                    # 实现分段睡眠，检查是否需要刷新页面
                    remaining_sleep = required_sleep_time
                    while remaining_sleep > 0:
                        # 检查是否需要刷新页面
                        if page_stay_time >= REFRESH_THRESHOLD:
                            print(f"页面停留时间已达 {page_stay_time} 秒，即将刷新页面以避免确认弹窗...")
                            # 记录未完成的学习时间
                            learning_interrupted = True
                            remaining_learning_time = remaining_sleep
                            print(f"学习中断，还有 {remaining_learning_time:.2f} 秒未完成")
                            
                            page.refresh()
                            time.sleep(5)  # 刷新后等待页面加载
                            page_stay_time = 0  # 重置停留时间
                            
                            # 刷新后重新点击当前内容继续学习
                            print(f"刷新后重新学习当前内容: {text}")
                            try:
                                # 重新查找并点击当前内容
                                item_elements = page.eles('.itemTitle')
                                found_and_clicked = False
                                for element in item_elements:
                                    if text in element.text:
                                        page.scroll.to_see(element)
                                        element.click()
                                        found_and_clicked = True
                                        print(f"成功重新点击: {text}")
                                        break
                                
                                # 如果通过.itemTitle没找到，尝试contains选择器
                                if not found_and_clicked:
                                    try:
                                        refresh_selector = page.ele(f'contains({text})')
                                        page.scroll.to_see(refresh_selector)
                                        refresh_selector.click()
                                        found_and_clicked = True
                                        print(f"成功通过contains选择器重新点击: {text}")
                                    except:
                                        print(f"刷新后未找到元素: {text}")
                                
                                # 如果成功重新点击，则继续完成剩余学习时间
                                if found_and_clicked:
                                    print(f"继续完成剩余学习时间: {remaining_learning_time:.2f} 秒")
                                    # 更新页面停留时间（包含刷新操作的时间）
                                    page_stay_time += 5  # 加回刷新等待时间
                                    
                                    # 重新实现分段睡眠，确保再次检查刷新阈值
                                    remaining_refresh_sleep = remaining_learning_time
                                    while remaining_refresh_sleep > 0:
                                        if page_stay_time >= REFRESH_THRESHOLD:
                                            print(f"页面停留时间再次达到阈值，再次刷新...")
                                            page.refresh()
                                            time.sleep(5)
                                            page_stay_time = 0
                                            break
                                        
                                        current_sleep = min(10, remaining_refresh_sleep)
                                        time.sleep(current_sleep)
                                        remaining_refresh_sleep -= current_sleep
                                        page_stay_time += current_sleep
                                    
                                    # 更新总页面停留时间
                                    if remaining_refresh_sleep <= 0:
                                        page_stay_time += remaining_learning_time
                            except Exception as refresh_e:
                                print(f"刷新后重新学习时出错: {str(refresh_e)}")
                            
                            # 跳出外层循环，继续处理下一个内容
                            break
                        
                        # 计算本次睡眠时长（最多10秒，或剩余睡眠时长）
                        current_sleep = min(10, remaining_sleep)
                        time.sleep(current_sleep)
                        remaining_sleep -= current_sleep
                        page_stay_time += current_sleep
                    
                    # 如果没有因为刷新而中断，更新页面停留时间
                    if remaining_sleep <= 0:
                        page_stay_time += required_sleep_time
                else:
                    # 如果找不到时间元素，使用默认的随机停顿时间
                    print(f"未找到时间元素，使用默认随机停顿时间: {sleep_time:.2f} 秒")
                    
                    # 实现分段睡眠，检查是否需要刷新页面
                    remaining_sleep = sleep_time
                    while remaining_sleep > 0:
                        # 检查是否需要刷新页面
                        if page_stay_time >= REFRESH_THRESHOLD:
                            print(f"页面停留时间已达 {page_stay_time} 秒，即将刷新页面以避免确认弹窗...")
                            page.refresh()
                            time.sleep(5)  # 刷新后等待页面加载
                            page_stay_time = 0  # 重置停留时间
                            break
                        
                        # 计算本次睡眠时长（最多10秒，或剩余睡眠时长）
                        current_sleep = min(10, remaining_sleep)
                        time.sleep(current_sleep)
                        remaining_sleep -= current_sleep
                        page_stay_time += current_sleep
                    
                    # 如果没有因为刷新而中断，更新页面停留时间
                    if remaining_sleep <= 0:
                        page_stay_time += sleep_time
            except Exception as time_e:
                # 如果处理时间时出错，使用默认停顿时间
                print(f"处理时间信息时出错: {str(time_e)}，使用默认随机停顿时间: {sleep_time:.2f} 秒")
                
                # 实现分段睡眠，检查是否需要刷新页面
                remaining_sleep = sleep_time
                while remaining_sleep > 0:
                    # 检查是否需要刷新页面
                    if page_stay_time >= REFRESH_THRESHOLD:
                        print(f"页面停留时间已达 {page_stay_time} 秒，即将刷新页面以避免确认弹窗...")
                        # 记录未完成的学习时间
                        learning_interrupted = True
                        remaining_learning_time = remaining_sleep
                        print(f"学习中断，还有 {remaining_learning_time:.2f} 秒未完成")
                        
                        page.refresh()
                        time.sleep(5)  # 刷新后等待页面加载
                        page_stay_time = 0  # 重置停留时间
                        
                        # 刷新后重新点击当前内容继续学习
                        print(f"刷新后重新学习当前内容: {text}")
                        try:
                            # 重新查找并点击当前内容
                            item_elements = page.eles('.itemTitle')
                            found_and_clicked = False
                            for element in item_elements:
                                if text in element.text:
                                    page.scroll.to_see(element)
                                    element.click()
                                    found_and_clicked = True
                                    print(f"成功重新点击: {text}")
                                    break
                            
                            # 如果通过.itemTitle没找到，尝试contains选择器
                            if not found_and_clicked:
                                try:
                                    refresh_selector = page.ele(f'contains({text})')
                                    page.scroll.to_see(refresh_selector)
                                    refresh_selector.click()
                                    found_and_clicked = True
                                    print(f"成功通过contains选择器重新点击: {text}")
                                except:
                                    print(f"刷新后未找到元素: {text}")
                            
                            # 如果成功重新点击，则继续完成剩余学习时间
                            if found_and_clicked:
                                print(f"继续完成剩余学习时间: {remaining_learning_time:.2f} 秒")
                                # 更新页面停留时间（包含刷新操作的时间）
                                page_stay_time += 5  # 加回刷新等待时间
                                
                                # 重新实现分段睡眠，确保再次检查刷新阈值
                                remaining_refresh_sleep = remaining_learning_time
                                while remaining_refresh_sleep > 0:
                                    if page_stay_time >= REFRESH_THRESHOLD:
                                        print(f"页面停留时间再次达到阈值，再次刷新...")
                                        page.refresh()
                                        time.sleep(5)
                                        page_stay_time = 0
                                        break
                                    
                                    current_sleep = min(10, remaining_refresh_sleep)
                                    time.sleep(current_sleep)
                                    remaining_refresh_sleep -= current_sleep
                                    page_stay_time += current_sleep
                                
                                # 更新总页面停留时间
                                if remaining_refresh_sleep <= 0:
                                    page_stay_time += remaining_learning_time
                        except Exception as refresh_e:
                            print(f"刷新后重新学习时出错: {str(refresh_e)}")
                        
                        # 跳出外层循环，继续处理下一个内容
                        break
                    
                    # 计算本次睡眠时长（最多10秒，或剩余睡眠时长）
                    current_sleep = min(10, remaining_sleep)
                    time.sleep(current_sleep)
                    remaining_sleep -= current_sleep
                    page_stay_time += current_sleep
                
                # 如果没有因为刷新而中断，更新页面停留时间
                if remaining_sleep <= 0:
                    page_stay_time += sleep_time
        else:
            print(f"警告: 未找到包含文本 '{text}' 的元素")
            # 尝试刷新页面
            page.refresh()
            time.sleep(5)
    except Exception as e:
        print(f"错误: 处理 '{text}' 时出现异常 - {str(e)}")
        # 尝试刷新页面
        page.refresh()
        time.sleep(5)
    
    # 计算当前循环用时和总用时
    loop_duration = time.time() - loop_start_time
    total_duration = time.time() - start_time
    
    # 报告每轮循环结束的总用时，使用分:秒格式
    print(f"循环 {i+1}/{len(name_list)} 完成，当前循环用时: {format_time(loop_duration)}，总用时: {format_time(total_duration)}")
            

# 循环结束后再次检查已学时长
print("\n所有学习内容处理完成，检查最终学习时长...")
try:
    # 获取已学时长元素
    study_time_ele = page.ele('.text-1')
    if study_time_ele:
        final_study_time = study_time_ele.text
        final_study_seconds = time_str_to_seconds(final_study_time)
        
        # 显示最终学习进度
        final_progress_percentage = (final_study_seconds / REQUIRED_TOTAL_SECONDS) * 100
        print(f"最终已学习时间: {final_study_time}，进度: {final_progress_percentage:.1f}%")
        
        if final_study_seconds >= REQUIRED_TOTAL_SECONDS:
            print(f"恭喜！已完成{REQUIRED_TOTAL_HOURS}小时的必学时长要求。")
        else:
            remaining_seconds = REQUIRED_TOTAL_SECONDS - final_study_seconds
            remaining_hours = remaining_seconds / 3600
            print(f"尚未完成必学时长要求。还需学习: {format_time(remaining_seconds)} ({remaining_hours:.1f}小时)")
except Exception as final_time_e:
    print(f"获取最终学习时长信息时出错: {str(final_time_e)}")

# 关闭浏览器
page.close()

# 打印总耗时
print(f"\n程序运行总耗时: {format_time(total_duration)}")
            
           
