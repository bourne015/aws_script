'''
    dependency:
        lxml: pip install lxml
'''
from bs4 import BeautifulSoup
import requests
import json
import csv
import argparse
import datetime

baseurl = "https://www.feixiaohao.com"
baseurl_ex = "https://www.feixiaohao.com/exchange/"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
headers = {"Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Host": "dncapi.bqiapp.com",
        "Origin": baseurl,
        "Referer": baseurl_ex,
        "User-Agent":user_agent,
        "Cache-Control": "max-age=0"}

class sse_connect():
    def __init__(self):
        self.filename = "ExchangeRanking_" +\
                    datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"
        self.csvheader = ['Rank', 'ID', '平台','ExRank' ,'24H额',
                '24H涨跌', '资产', '交易对', '人气指数',
                'Volume_BTC', 'Volume_CNY', '官网']

    def create_session(self):
        session = requests.Session()
        return session

    def sse_getdata(self, session, args):
        res, page, cnt = [], 1, args.n
        while cnt > 0:
            #req_cnt = 100 if cnt>100 else cnt
            test_url = "https://dncapi.bqiapp.com/api/v2/exchange/web-exchange"
            test_url += "?token=&page="+str(page)
            test_url += "&pagesize=100&sort_type="+args.st
            test_url += "&asc=1"
            test_url += "&isinnovation=1&type="+args.t
            test_url += "&area="+args.a+"&webp=1"
            req = session.get(test_url, headers=headers)
            if req:
                data = json.loads(req.text)
                res += data['data'][:cnt]
            cnt -= 100
            page += 1
        #print(self.csvheader)
        for x in res:
            print(x['rank'], x['id'], x['name'], x['exrank'], x['volumn'],
                  x['change_volumn'], x['assets_usd'], x['pairnum'], x['hotindex'],
                  x['volumn_btc'], x['volumn_cny'])

        #print(res[0])
        return res

    def get_website(self, session, data):
        for x in data:
            btc_website = ''
            sub_url = baseurl_ex + x['id']
            req = session.get(sub_url)
            soup = BeautifulSoup(req.text, 'lxml')
            btc_website_all = soup.findAll("a", {'class':{}, "style":{},
                                "target":{"_blank"}, "rel":{"nofollow"}})
            if btc_website_all:
                btc_website = btc_website_all[0].get('href')
            #print(btc_website)
            x['btc_website'] = btc_website if btc_website else 'none'

    def save_data(self, data):
        with open(self.filename,'w',newline='', encoding='utf-8-sig') as f:
            #fd = csv.DictWriter(f, self.csvheader)
            #fd.writeheader()
            fd = csv.writer(f)
            fd.writerow(self.csvheader)
            for x in data:
                row = [x['rank'], x['id'], x['name'], x['exrank'],
                        x['volumn'], str(x['change_volumn'])+'%',
                        x['assets_usd'], x['pairnum'], x['hotindex'],
                        x['volumn_btc'], x['volumn_cny'], x['btc_website']]
                fd.writerow(row)
        print("saved data in", self.filename)

    def close_session(self, session):
        session.close()

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.description='''e.g.\
                 python req.py -n 110'''
    parser.add_argument('-n', help='total number',  type=int, default=150)
    parser.add_argument('-st', help='sort type: [exrank|volume|change|assets|pairs|hot]',
                        type=str,default='exrank')
    parser.add_argument('-a', help='area: []',  type=str, default='')
    parser.add_argument('-t', help='transaction type: [all|spot|futures|fiat|otc]',
                        type=str, default='all')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = argument_parser()
    conn = sse_connect()
    session = conn.create_session()
    data = conn.sse_getdata(session, args)
    if data:
        conn.get_website(session, data)
        conn.save_data(data)
    conn.close_session(session)

