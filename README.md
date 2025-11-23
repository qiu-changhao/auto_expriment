# auto_expriment
自动刷USTC实验室安全教育视频以及自动考试
## 首先安装drissionpage库
pip install DrissionPage
## 运行drissionpage_init.py进行初始化，仅首次使用时需要初始化
需要经默认浏览器.exe文件的路径替换成你自己的
## 运行get_name.py获取名称列表
![](images/name_list.png)
一共三十几个名字，但是一次最多获取三十个，所以需要多跑一两次
## 运行auto_expriment.py自动学习
![](images/auto_expriment.png)
需要多运行一两次

首次打开浏览器需要登陆，之后短期内就不需要了。该程序会统计已学习时长与总时长，然后进行学习，因为页面五分钟就会有一个确认，我们在五分钟前进行一次刷新。当学习时间达到要求学习时长后就会停止并报告。
