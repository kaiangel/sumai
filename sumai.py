import os
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask_socketio import emit

chrome_options = Options()
chrome_options.add_argument("--headless")
webdriver_service = Service(ChromeDriverManager().install())
import openai
import time

def get_article_text(url, sid):
    driver = None
    try:
        print("Setting up WebDriver...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.get(url)

        print("Scrolling the webpage...")
        SCROLL_PAUSE_TIME = 1
        last_height = driver.execute_script("return document.body.scrollHeight")
        emit('status', {'message': '正在浏览内容......'}, room=sid)  # 新增

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            time.sleep(3)

        print("Extracting content...")
        emit('status', {'message': '正在获取内容......'}, room=sid)  # 新增
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        if "amt.com.cn" in url:
            article = soup.find("div", class_="article_body")
            if article:
                article = article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'section', 'article', 'blockquote', 'div'])
            else:
                raise ValueError("无法从网页中提取文本。")
        else:
            article = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'section', 'article', 'blockquote', 'div'])
            if not article:
                article = soup.find('body')
                if article:
                    article = article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'section', 'article', 'blockquote', 'div'])

        if not article:
            raise ValueError("无法从网页中提取文本。")

        text = ' '.join([elem.get_text() for elem in article])
        
        print(f"获取到文章内容共{len(text)}个中文文字")
        emit('status', {'message': '已成功获取内容，魔法将大约在半分钟后诞生......'}, room=sid)  # 新增
        return text
    
    except TimeoutException as e:
        return f"TimeoutException: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        if driver:
            driver.quit()

def generate_summary(text):
    print("Generating summary...")
    openai.api_key = os.environ["OPENAI_KEY"]

    truncated_text = text[:2680]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "你是一个专业的泛阅读内容分析师，专注于为在中国一二线城市忙碌的人们提供精炼且深入的全文总结。"},
                {"role": "user", "content": f"以markdown的形式总结以下内容：\n\n{truncated_text}\n\n我希望得到一篇能在3分钟内看完的总结，包括以下6要素：1. 主题和主要观点 2. 支持细节（支持主要观点的证据或例子。） 3. 作者可能的目的和目标受众 4. 风格和语调 5. 结论或结尾（包括且不限于作者的结论或对读者的呼吁等） 6. 全文中关键词和术语的解释。另外，请用全文中生动有趣的现实例子帮助我更好地理解和吸收这些内容，如果在全文中没有找到合适的现实例子，你可以自行展开想象并提供与要点以及结论相关且生动有趣易懂的例子，我希望读完这个总结后我的对全文内容的理解和消化好于我自己阅读全文。确保一定要以markdown的形式。"},
            ],
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.8,
        )

        summary = response.choices[0].message['content'].strip()
        
        print("Summary generated.")
        return summary  # 返回完整摘要
    except Exception as e:
        print(f"An error occurred while generating the summary: {e}")
        return None