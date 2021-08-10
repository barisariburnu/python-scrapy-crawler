import json
import os
import shutil
from scrapy import spiders, Request
from datetime import datetime
from udemy import settings
from udemy.items import UdemyItemParser
from udemy.settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
from pymongo import MongoClient

client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@ireland.xjelg.mongodb.net/{MONGO_DATABASE}"
    f"?retryWrites=true&w=majority"
)
db = client.get_default_database()


class UdemySpider(spiders.CrawlSpider):
    name = 'udemy'
    allowed_domains = ['udemy.com']
    start_urls = ['https://udemy.com']

    def start_requests(self):
        """""
        CATEGORY_IDs dizisinde belirtilen tüm kategorilerin adres bilgisini oluşturur.
        Oluşturduğu tüm adreslerine istek atar.
        """""
        for ids in settings.CATEGORY_IDs:
            url = f'{settings.BASE_URL}{settings.ALL_COURSE_URL}/?category_id={ids}&{settings.PARAMS}'
            yield Request(url=url, callback=self.parse_pagination, cb_kwargs=dict(category_id=ids))

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
            url = f'{settings.BASE_URL}{settings.ALL_COURSE_URL}/?category_id={category_id}&{settings.PARAMS}&p={page}'
            yield Request(url=url, callback=self.parse_list_page)

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

            if item['last_update_date'] is not None:
                created = item['last_update_date']
            else:
                date = datetime.strptime(item['created'], "%Y-%m-%dT%H:%M:%SZ")
                created = date.strftime('%Y-%m-%d')

            if db.course.find_one({"$and": [{"cid": ids}, {created: created}]}):
                print('Already exists course: {0}'.format(ids))
                return

            url = f"{settings.BASE_URL}/courses/{ids}/?fields[course]=@all"
            yield Request(url=url, callback=self.parse_item)

    def parse_item(self, response):
        """""
        parse_list_page içerisinden yapılan istekler sonucunda gelen cevapları alır.
        Eğitimin tüm içeriği parse edilir.
        """""
        data = json.loads(response.body)
        item = UdemyItemParser(data)

        if item.price == 'Free':
            if not os.path.isdir(item.absolute_path):
                os.makedirs(item.absolute_path)

            try:
                item.download_thumbnail()
                item.save_to_mdx()
            except Exception as ex:
                shutil.rmtree(item.absolute_path)
                print(f'Error : {ex}')
                return

        return item.export_to_json()
