# 导入ChromiumPage
from DrissionPage import ChromiumPage
from pprint import pprint
# 打开浏览器
page = ChromiumPage()
# 监听数据包
page.listen.start('https://sysaq.ustc.edu.cn/cg-exam-server/api/page_study_content?page=0&size=30&type=1&examId=5&nocache')
# 打开第一页
page.get('https://sysaq.ustc.edu.cn/lab-study-front/examTask/5/4/1/42')
# 等待数据包加载完成
rep = page.listen.wait()
# 打印响应数据
name_list=[]
for item in rep.response.body['data']['content']:
    name_list.append(item['title'])

# 将name_list中的内容按行存储到txt文件
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, 'name_list.txt'), 'w', encoding='utf-8') as f:
    for name in name_list:
        f.write(name + '\n')
        
print(f"已成功将{len(name_list)}条数据保存到name_list.txt文件中。")


