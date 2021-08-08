# -*- coding: utf-8 -*-

import os
import logging
import pickledb
from scrapy.exceptions import DropItem
from udemy.settings import DATA_PATH


logger = logging.getLogger(__name__)
db = pickledb.load(os.path.join(DATA_PATH, 'udemy.db'), True)


class UdemyPipeline(object):
    def __init__(self):
        self.post_seen = set()

    def process_item(self, item, spider):
        if item['cid'] in self.post_seen:
            raise DropItem(f"Duplicate item found: {item['cid']}")

        try:
            if db.set(item['cid'], item):
                logger.info('Successful course id: {0}'.format(item['cid']))
                self.post_seen.add(item['cid'])
            else:
                logger.error('Error course id: {0}'.format(item['cid']))
                raise DropItem(f"Error item: {item['cid']}")
        except Exception as ex:
            raise DropItem(ex)

        return item
