#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import scrapy
import random
import requests
from udemy import settings
from slugify import slugify
from datetime import datetime
from udemy.user_agents import USER_AGENT_LIST


class UdemyItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    slug = scrapy.Field()
    permanent_url = scrapy.Field()
    headline = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    image_url = scrapy.Field()
    created = scrapy.Field()
    instructional_level = scrapy.Field()
    content_info = scrapy.Field()


class UdemyItemParser(object):
    def __init__(self, response):
        self.response = response

    @property
    def id(self):
        result = str(self.response['id'])
        return result

    @property
    def title(self):
        result = self.response['title'].replace(':', ' -').replace('  ', ' ').replace("'", "''")
        return result

    @property
    def slug(self):
        result = self.response['published_title']
        return result

    @property
    def permanent_url(self):
        result = f"{slugify(self.category.replace('&', 'and').lower())}/{self.slug}"
        return result

    @property
    def headline(self):
        result = self.response['headline'].replace('  ', ' ')
        return result

    @property
    def category(self):
        result = self.response['primary_category']['title']
        return result

    @property
    def subcategory(self):
        result = self.response['primary_subcategory']['title']
        return result

    @property
    def image_url(self):
        result = self.response['image_750x422']
        return result

    @property
    def created(self):
        if self.response['last_update_date'] is not None:
            result = self.response['last_update_date']
        else:
            date = datetime.strptime(self.response['created'], "%Y-%m-%dT%H:%M:%SZ")
            result = date.strftime('%Y-%m-%d')
        return result

    @property
    def instructional_level(self):
        result = self.response['instructional_level']
        return result

    @property
    def content_info(self):
        result = self.response['content_info']
        return result

    def export_to_json(self):
        return dict(
            _id=self.id,
            title=self.title,
            slug=self.slug,
            permanent_url=self.permanent_url,
            headline=self.headline,
            image_url=self.image_url,
            category=self.category,
            subcategory=self.subcategory,
            created=self.created,
            instructional_level=self.instructional_level,
            content_info=self.content_info,
            shared=0
        )
