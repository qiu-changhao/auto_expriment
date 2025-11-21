初始化drimmsionpage
from DrissionPage import ChromiumOptions
# 设置浏览器路径
path=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
ChromiumOptions().set_browser_path(path).save()