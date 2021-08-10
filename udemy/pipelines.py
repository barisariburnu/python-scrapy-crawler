# -*- coding: utf-8 -*-

import logging
from scrapy.exceptions import DropItem
from udemy.settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
from pymongo import MongoClient

client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@ireland.xjelg.mongodb.net/{MONGO_DATABASE}"
    f"?retryWrites=true&w=majority"
)
db = client.get_default_database()
logger = logging.getLogger(__name__)


class UdemyPipeline(object):
    def __init__(self):
        self.post_seen = set()

    def process_item(self, item, spider):
        if item['cid'] in self.post_seen:
            raise DropItem(f"Duplicate item found: {item['cid']}")

        try:
            if str(db.course.insert_one(item)):
                logger.info('Successful course id: {0}'.format(item['cid']))
                self.post_seen.add(item['cid'])
            else:
                logger.error('Error course id: {0}'.format(item['cid']))
                raise DropItem(f"Error item: {item['cid']}")
        except Exception as ex:
            raise DropItem(ex)

        return item
