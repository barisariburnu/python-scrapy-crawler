import os
import scrapy
import json
import requests
import shutil
import config
from pymongo import MongoClient
from crawler.spiders.udemy.items import UdemyItemParser

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

CLIENT = MongoClient(
    f'mongodb://{config.MONGO_USERNAME}:{config.MONGO_PASSWORD}@'
    f'ireland-shard-00-00.xjelg.mongodb.net:27017,'
    'ireland-shard-00-01.xjelg.mongodb.net:27017,'
    'ireland-shard-00-02.xjelg.mongodb.net:27017/crawler?'
    'ssl=true&replicaSet=atlas-nrk72v-shard-0&authSource=admin&retryWrites=true&w=majority'
)
DB = CLIENT.get_default_database()


class UdemySpider(scrapy.spiders.CrawlSpider):
    name = 'udemy'
    allowed_domains = ['udemy.com']
    start_urls = ['https://udemy.com']

    def start_requests(self):
        for ids in config.CATEGORY_IDs:
            url = f'{config.BASE_URL}{config.ALL_COURSE_URL}/?category_id={ids}&{config.PARAMS}'
            yield scrapy.Request(url=url, callback=self.parse_pagination, cb_kwargs=dict(category_id=ids))

    def parse_pagination(self, response, category_id):
        data = json.loads(response.body)
        total_page = data['unit']['pagination']['total_page']

        for page in range(1, total_page + 1):
            url = f'{config.BASE_URL}{config.ALL_COURSE_URL}/?category_id={category_id}&{config.PARAMS}&p={page}'
            yield scrapy.Request(url=url, callback=self.parse_list_page)

    def parse_list_page(self, response):
        data = json.loads(response.body)
        unit = data['unit']

        for item in unit['items']:
            ids = item['id']
            url = f"{config.BASE_URL}/courses/{ids}/?fields[course]=@all"
            yield scrapy.Request(url=url, callback=self.parse_item)

    def parse_item(self, response):
        data = json.loads(response.body)
        item = UdemyItemParser(data)

        if not os.path.isdir(BASE_PATH):
            os.makedirs(BASE_PATH)

        try:
            img_path = os.path.join(BASE_PATH, item.thumbnail)
            with open(img_path, "wb") as f:
                r = requests.get(data['image_750x422'])
                f.write(r.content)
        except Exception as ex:
            shutil.rmtree(BASE_PATH)
            print(f'Download Image Error : {ex}')
            return

        try:
            mdx_path = os.path.join(BASE_PATH, f'{item.slug}')
            with open(mdx_path, 'w', encoding='utf8') as f:
                r = item.export_to_markdown()
                f.write(r)
        except Exception as ex:
            shutil.rmtree(BASE_PATH)
            print(f'Save MDX File Error : {ex}')
            return

        if str(DB.udemy.insert_one(item.export_to_json())):
            print(f'Successul: {item.permanent_url}')

        return item.export_to_json()
