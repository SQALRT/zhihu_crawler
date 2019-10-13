import requests
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
import pymongo
client = pymongo.MongoClient('localhost')
db = client['zhihu']
# from selenium import webdriver
base_url = "https://www.zhihu.com/hot"
proxy_pool_url = 'https://127.0.0.1:5010/get'
proxy = None
Max_count = 5
headers = {
    'cookie': '_zap=bda6b711-af6f-4ec5-83d2-4637f43d4bdc; d_c0="AIDjTtG00A-PTp68alG4H8o98rEOHc8gmDA=|1564484081"; q_c1=4ad55bb1451f4f06bb5a86ce747057ee|1565062551000|1565062551000; tgw_l7_route=73af20938a97f63d9b695ad561c4c10c; _xsrf=56ac7c03-143c-4c2d-9520-43880abf4658; capsion_ticket="2|1:0|10:1565837006|14:capsion_ticket|44:YzNkMzk2YTQ0MjVhNGRkN2I2M2FjNTVkNzVkNjFhMDE=|b9ce4f889dcdced6addeb4924a9507f7ddffd456cf590da84d6e28509df758bf"; l_n_c=1; r_cap_id="MTBkZDkxNmQ2NzJjNDk5YjgwN2ZkODIzMDE2ODY0Nzk=|1565837013|caf334ae4ee9473dad3b040386686612252d6bfc"; cap_id="NzM0NjAxOTMwMzVjNDRiN2FjMjRiZWE5NDcyMGRhZDg=|1565837013|97c32a3fecd2e6de3b2bb122891c7de9ecea0590"; l_cap_id="MDgxMDliY2YzNzk0NGE0ODg5YjI3YTljNDhmNzJhZmI=|1565837013|6446840995bfad71a3d8478cfc8331d0b3a3c6b4"; n_c=1; z_c0=Mi4xVmZZQ0J3QUFBQUFBZ09OTzBiVFFEeGNBQUFCaEFsVk42QlJDWGdDaXk3cjQzNVhSZi1kV2NSb3VIVXV4SVJVeUF3|1565837032|621b4d0e426aaf6f90fa37710b74fc1e8f471679; tst=r',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
}
head ={
    'upgrade-insecure-requests':'1',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
}

response = requests.get(base_url, headers=headers)


def get_proxy():
    try:
        respose = requests.get(proxy_pool_url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionAbortedError as ce:
        return None


def get_html(url, count=1):
    print("crawling", url)
    print('try counting', count)
    global proxy
    if count >= Max_count:
        print("too many try")
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://'+proxy
            }
            response = requests.get(
                url, allow_redirects=False, headers=headers, proxies=proxies)
        else:
            response = requests.get(
                url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            print('302')
            pass
        proxy = get_proxy()
        if proxy:
            print('using proxy', proxy)
            return get_html(url)
        else:
            print('get proxy failed')
            return None
    except ConnectionError as e:
        print('error occured', e.args)
        count += 1
        proxy = get_proxy()
        return get_html(url, count)


def parse_index(html):
    doc = pq(html)
    items = doc("section .HotItem-content a").items()
    for item in items:
        yield item.attr('href')
        
        
def get_detail(url):
    try:
        response = requests.get(url,headers = head)
        return response.text
    except ConnectionError:
        return None

def parse_detail(html):
    doc = pq(html)
    items = doc("#QuestionAnswers-answers > div > div > div > div:nth-child(2) > div").items()
    for item in items:
        number = item("div:nth-child(1) > div > div.ContentItem-meta > div.AnswerItem-extraInfo > span > button").text()
        author = item("div:nth-child(1) > div > div.ContentItem-meta > div.AuthorInfo.AnswerItem-authorInfo.AnswerItem-authorInfo--related > meta:nth-child(1)")
        author = author.attr('content')
        content = item('div:nth-child(1) > div > div.RichContent.RichContent--unescapable > div.RichContent-inner').text()
        yield{
            'number':number,
            'author':author,
            'content':content
        }

def save_to_db(data):
    if db['articles'].update({'author':data['author']},{'$set':data},True):
        print('saved to mongo',data['author'])
    else:
        print('saved to mongo failed',data[title])
def main():
#     print(get_detail())
    html = get_html(base_url)
    articles = parse_index(html)
#     print(articles)
    for article in articles:
        detail_html = get_detail(article)
        result = parse_detail(detail_html)
        for i in result:
            save_to_db(i)




if __name__ == "__main__":
    main()
