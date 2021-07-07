import os
import scrapy
import json
import requests
import shutil
from crawler.spiders.udemy import config
from pymongo import MongoClient
from crawler.spiders.udemy.items import UdemyItemParser, BASE_PATH

client = MongoClient(
    f'mongodb://{config.MONGO_USERNAME}:{config.MONGO_PASSWORD}@'
    f'ireland-shard-00-00.xjelg.mongodb.net:27017,'
    'ireland-shard-00-01.xjelg.mongodb.net:27017,'
    'ireland-shard-00-02.xjelg.mongodb.net:27017/crawler?'
    'ssl=true&replicaSet=atlas-nrk72v-shard-0&authSource=admin&retryWrites=true&w=majority'
)
db = client.get_default_database()


class UdemySpider(scrapy.spiders.CrawlSpider):
    name = 'udemy'
    allowed_domains = ['udemy.com']
    start_urls = ['https://udemy.com']

    def start_requests(self):
        """""
        CATEGORY_IDs dizisinde belirtilen tüm kategorilerin adres bilgisini oluşturur.
        Oluşturduğu tüm adreslerine istek atar.
        """""
        for ids in config.CATEGORY_IDs:
            url = f'{config.BASE_URL}{config.ALL_COURSE_URL}/?category_id={ids}&{config.PARAMS}'
            yield scrapy.Request(url=url, callback=self.parse_pagination, cb_kwargs=dict(category_id=ids))

    def parse_pagination(self, response, category_id):
        """""
        start_requests içerisinden yapılan istekler sonucunda gelen cevapları alır.
        İlgili kategoride toplam kaç sayfa içerik olduğu bilgisini parse eder.
        Kategoriye ait toplam sayfa sayısını kullanarak kategorinin tüm sayfa taleplerini oluşturur.
        Oluşturduğu tüm adreslere istek atar. 
        """""
        data = json.loads(response.body)
        total_page = data['unit']['pagination']['total_page']

        for page in range(1, total_page + 1):
            url = f'{config.BASE_URL}{config.ALL_COURSE_URL}/?category_id={category_id}&{config.PARAMS}&p={page}'
            yield scrapy.Request(url=url, callback=self.parse_list_page)

    def parse_list_page(self, response):
        """""
        parse_pagination içerisinden yapılan istekler sonucunda gelen cevapları alır.
        Her sayfada maks 60 eğitim içeriği (son sayfa değilse) gelmesi beklenir.
        Tüm eğitim bilgilerini parse eder ve detay sayfalarına ait adresi oluşturur.
        Oluşturduğu adrese istek atar. 
        """""
        data = json.loads(response.body)
        unit = data['unit']

        for item in unit['items']:
            ids = item['id']
            url = f"{config.BASE_URL}/courses/{ids}/?fields[course]=@all"
            yield scrapy.Request(url=url, callback=self.parse_item)

    def parse_item(self, response):
        """""
        parse_list_page içerisinden yapılan istekler sonucunda gelen cevapları alır.
        Eğitimin tüm içeriği parse edilir. Veritabanındaki kayıt bilgisi kontrol edilir.
        Thumbnail indirilir. MDX dosyası oluşturulur. Veritabanına kayıt edilir.
        """""
        data = json.loads(response.body)
        item = UdemyItemParser(data)

        if db.udemy.find_one({"cid": item.cid, "created": item.created}):
            print('Already exists posts: {0}'.format(item.cid))
            return

        if not os.path.isdir(item.absolute_path):
            os.makedirs(item.absolute_path)

        try:
            item.download_thumbnail()
            item.save_to_mdx()
        except Exception as ex:
            shutil.rmtree(item.absolute_path)
            print(f'Error : {ex}')
            return

        if str(db.udemy.insert_one(item.export_to_json())):
            print(f'Successul: {item.permanent_url}')

        return item.export_to_json()
