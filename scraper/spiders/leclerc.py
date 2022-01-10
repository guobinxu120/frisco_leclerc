# -*- coding: utf-8 -*-
from scrapy import Spider, Request
# from urlparse import urlparse
import sys
# import re, os, requests, urllib
# from scrapy.utils.response import open_in_browser
from collections import OrderedDict
# import time
# from shutil import copyfile
# from xlrd import open_workbook
import json, re, csv
# from validate_email import validate_email



class LeclercSpider(Spider):
    name = "leclerc"
    start_urls = ['https://ssl.leclerc.com.pl/ssl/',]

    use_selenium = False
    count = 0
    total = 0
    reload(sys)
    sys.setdefaultencoding('utf-8')
    units = ['kg', 'g', 'szt','L', 'ml', 'para', 'pary', 'cm']
    headers = {
                'Host': 'angel.co',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'en-US,en;q=0.8',
                'Cookie': 'intercom-id-og2vxfl5=1ca11f39-d87c-40ce-a608-a220d8e5e980; ajs_anonymous_id=%226b6ea0b7-b64f-4e85-b717-4b60c9912784%22; _ga=GA1.2.567149796.1514406722; _gid=GA1.2.1678712760.1514864845; ajs_group_id=null; ajs_user_id=%227305367%22; _angellist=a71a277ab05568d2fe069eb936c75c05; amplitude_idangel.co=eyJkZXZpY2VJZCI6IjU5MWU0NTQwLWI2YmItNGRjNi1iZGZiLTUwMTk0OTI4Nzg3ZVIiLCJ1c2VySWQiOiI3MzA1MzY3Iiwib3B0T3V0IjpmYWxzZSwic2Vzc2lvbklkIjoxNTE1MDg3MTAzNDk0LCJsYXN0RXZlbnRUaW1lIjoxNTE1MDg4MDM1MjYwLCJldmVudElkIjoyMDEsImlkZW50aWZ5SWQiOjI1NCwic2VxdWVuY2VOdW1iZXIiOjQ1NX0=; _gat=1',
                'If-None-Match': 'W/"b42e1a728069ee24c32f7b180e165727"',
                # 'X-CSRF-Token': '6mr8EeXtLQurR32ZwHcDHEEKHoL544riKhvqVv5NMQtdpaWeXnvlIUXW3cjZj7uzzEuZhqnvfqfh+zbWhnj6RQ==',
                # 'X-Requested-With': 'XMLHttpRequest'
            }
    cookies = {'_angellist' :'a71a277ab05568d2fe069eb936c75c05'}


    def parse(self, response):
        cats = response.xpath('//ul[contains(@class, "main-menu")]/li/a/@href').extract()
        for cat in cats:
            yield Request(response.urljoin(cat), callback=self.parse_list)
                    # break

    def parse_list(self, response):
        item_tags = response.xpath('//div[contains(@class, "product-item")]')
        print response.url
        print len(item_tags)
        self.total += 1
        print "total: " +str(self.total)
        for item_tag in item_tags:
            item = OrderedDict()
            item['name'] = item_tag.xpath('.//h2[@class="prd_title"]/a/@title').extract_first()
            if not item['name']:
                continue
            item['url'] = response.urljoin(item_tag.xpath('.//h2[@class="prd_title"]/a/@href').extract_first())
            digit_amount = re.findall('[.\d]*[,\d]+', item['name'])

            amount = ''
            if len(digit_amount) > 0:
                unit = item['name'].strip().split(digit_amount[-1])[-1]
                if len(unit) < 7 and unit != '' and unit != ')':
                    amount = digit_amount[-1] + item['name'].strip().split(digit_amount[-1])[-1]
            price= item_tag.xpath('.//p[@class="price"]/text()').re('[.\d]*[,\d]+')[0]
            # price2 = item_tag.xpath('.//span[@class="price_decimals"]/text()').extract_first()
            # if not price2:
            #     price2 = '00'
            # price = price1 +'.'+ price2
            item['price'] = price
            item['currency'] = 'zł'
            if amount != '' :
                item['amount'] = amount.replace(',', '.')
            else:
                item['amount'] = ''
            if item['url']:
                yield Request(item['url'], callback= self.parse_final, meta={'item': item})

    def parse_final(self, response):
        item = response.meta['item']
        ean = response.xpath('//p[@style="padding:4px"]/text()').re('[.\d]+')[0]
        if len(ean) > 1:
            item['ean'] = ean
        else:
            item['ean'] = ''
        item['description'] = '\n'.join(response.xpath('//p[@class="itefulldescrption"]//text()').extract())
        item['image_url'] = response.urljoin(response.xpath('//img[@id="img_big"]/@src').extract_first())
        item['brand'] = item['name'].strip().split(' ')[0]
        if item['amount'] == '':
            item['amount'] = '1szt.'
        yield item

    #     data = json.loads(response.body)
    #     if len(data['data']) > 0:
    #         domain = data['data'][0]
    #         name = response.meta['item']['Username'].replace(' ', '%20')
    #         domain_name = domain['domain']
    #
    #         yield Request("https://api.hunter.io/v2/email-finder?domain=" + domain_name + "&full_name=" + name + "&api_key=b7b85fcdbe39d1ad79ba7e1510f6afcfb4d8e9a6&format=json",
    #                       callback=self.parse_email, meta={'item':response.meta['item'], 'domains': data['data'], 'domain': domain_name, 'firm':response.meta['firm']})
    #     else:
    #         item = response.meta['item']
    #         firms = item['Firms'].split(',')
    #         if len(firms) - 1 > response.meta['firm']:
    #                 yield Request("https://api.hunter.io/v2/domains-suggestion?query=" + firms[response.meta['firm'] + 1], callback= self.parse, meta={'item' : item, 'firm':response.meta['firm'] + 1})
    #
    #
    # def parse_email(self, response):
    #
    #     data = json.loads(response.body)
    #     if data['data']['email']:
    #         item = response.meta['item']
    #         item['Email'] = data['data']['email']
    #         yield Request('https://api.hunter.io/v2/email-verifier?email=' + item['Email'].replace('@','%40') + '&api_key=b7b85fcdbe39d1ad79ba7e1510f6afcfb4d8e9a6&format=json',
    #                       callback=self.validate_email, meta={'item':item, 'domains': response.meta['domains'], 'domain': response.meta['domain'], 'firm':response.meta['firm']})
    #         # yield item
    #     else:
    #         flag = False
    #         item = response.meta['item']
    #         if len(response.meta['domains']) > 0 and response.meta['domain'] == response.meta['domains'][len(response.meta['domains']) -1]['domain']:
    #             firms = item['Firms'].split(',')
    #             if len(firms) - 1 > response.meta['firm']:
    #                 yield Request("https://api.hunter.io/v2/domains-suggestion?query=" + firms[response.meta['firm']+1], callback= self.parse, meta={'item' : item, 'firm':response.meta['firm']+1})
    #         else:
    #             for domain in response.meta['domains']:
    #                 if domain['domain'] == response.meta['domain']:
    #                     flag = True
    #                 elif flag:
    #                     domain_name = domain['domain']
    #                     name = response.meta['item']['Username'].replace(' ', '%20')
    #                     yield Request("https://api.hunter.io/v2/email-finder?domain=" + domain_name + "&full_name=" + name + "&api_key=b7b85fcdbe39d1ad79ba7e1510f6afcfb4d8e9a6&format=json",
    #                               callback=self.parse_email, meta={'item':response.meta['item'], 'domains': response.meta['domains'], 'domain': domain_name, 'firm':response.meta['firm']})
    #                     break
    #
    # def validate_email(self, response):
    #     data = json.loads(response.body)
    #     if data['data']['result'] != 'deliverable':
    #         # pass
    #         flag = False
    #         item = response.meta['item']
    #         if len(response.meta['domains']) > 0 and response.meta['domain'] == response.meta['domains'][len(response.meta['domains']) -1]['domain']:
    #             firms = item['Firms'].split(',')
    #             if len(firms) - 1 > response.meta['firm']:
    #                 yield Request("https://api.hunter.io/v2/domains-suggestion?query=" + firms[response.meta['firm']+1], callback= self.parse, meta={'item' : item, 'firm':response.meta['firm']+1})
    #         else:
    #             for domain in response.meta['domains']:
    #                 if domain['domain'] == response.meta['domain']:
    #                     flag = True
    #                 elif flag:
    #                     domain_name = domain['domain']
    #                     name = response.meta['item']['Username'].replace(' ', '%20')
    #                     yield Request("https://api.hunter.io/v2/email-finder?domain=" + domain_name + "&full_name=" + name + "&api_key=b7b85fcdbe39d1ad79ba7e1510f6afcfb4d8e9a6&format=json",
    #                               callback=self.parse_email, meta={'item':response.meta['item'], 'domains': response.meta['domains'], 'domain': domain_name, 'firm':response.meta['firm']})
    #                     break
    #     else:
    #         yield response.meta['item']

