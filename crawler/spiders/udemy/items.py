#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import scrapy
import requests
import html2markdown
from slugify import slugify
from datetime import datetime

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


class UdemyItem(scrapy.Item):
    cid = scrapy.Field()
    version = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    slug = scrapy.Field()
    permanent_url = scrapy.Field()
    headline = scrapy.Field()
    thumbnail = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    tags = scrapy.Field()
    keywords = scrapy.Field()
    created = scrapy.Field()
    description = scrapy.Field()
    requirements_data = scrapy.Field()
    what_you_will_learn_data = scrapy.Field()
    who_should_attend_data = scrapy.Field()
    captions = scrapy.Field()
    instructional_level = scrapy.Field()
    content_info = scrapy.Field()
    faq = scrapy.Field()
    price = scrapy.Field()


class UdemyItemParser(object):
    def __init__(self, response):
        self.response = response

    @property
    def cid(self):
        result = self.response['id']
        return result

    @property
    def version(self):
        date = datetime.strptime(self.created, '%Y-%m-%d')
        result = date.strftime('%y%m%d')
        return result

    @property
    def url(self):
        result = self.response['url']
        return result

    @property
    def title(self):
        result = self.response['title'].replace(':', ' -').replace('  ', ' ')
        return result

    @property
    def slug(self):
        result = self.response['published_title']
        return result

    @property
    def permanent_url(self):
        result = f"{slugify(self.category.replace('&', 'and').lower())}/{self.version}/{self.slug}"
        return result

    @property
    def headline(self):
        result = self.response['headline'].replace('  ', ' ')
        return result

    @property
    def thumbnail(self):
        result = f'{self.slug}.jpg'
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
    def tags(self):
        result = [f'#{slugify(self.category, to_lower=True)}']

        if self.subcategory:
            result.append(f'#{slugify(self.subcategory, to_lower=True)}')

        return result

    @property
    def keywords(self):
        result = [
            f'Real Course Discounts',
            f'Udemy',
            f'{self.category}'
        ]

        if self.subcategory:
            result.append(f'{self.subcategory}')

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
    def description(self):
        result = self.response['description'] \
            .replace('<li><p>', '<li>') \
            .replace('</p></li>', '</li>') \
            .replace(' style=""', '')
        return result

    @property
    def requirements_data(self):
        if self.response['requirements_data']['items'] is None \
                or self.response['requirements_data']['items'] == '':
            return None

        result = self.response['requirements_data']['items']
        return result

    @property
    def what_you_will_learn_data(self):
        if self.response['what_you_will_learn_data']['items'] is None \
                or self.response['what_you_will_learn_data']['items'] == '':
            return None

        result = self.response['what_you_will_learn_data']['items']
        return result

    @property
    def who_should_attend_data(self):
        if self.response['who_should_attend_data']['items'] is None \
                or self.response['who_should_attend_data']['items'] == '':
            return None

        result = self.response['who_should_attend_data']['items']
        return result

    @property
    def captions(self):
        if self.response['caption_languages'] is None \
                or self.response['caption_languages'] == '':
            return None

        result = self.response['caption_languages']
        return result

    @property
    def instructional_level(self):
        result = self.response['instructional_level']
        return result

    @property
    def content_info(self):
        result = self.response['content_info']
        return result

    @property
    def faq(self):
        result = self.response['faq']
        return result

    @property
    def price(self):
        return self.response['price']

    @property
    def absolute_path(self):
        return os.path.join(BASE_PATH, self.permanent_url)

    def download_thumbnail(self):
        path = os.path.join(self.absolute_path, self.thumbnail)
        with open(path, "wb") as f:
            data = requests.get(self.response['image_750x422'])
            f.write(data.content)

    def save_to_mdx(self):
        path = os.path.join(self.absolute_path, f'{self.slug}.mdx')
        with open(path, "w", encoding='utf8') as f:
            data = self.export_to_markdown()
            f.write(data)

    def export_to_json(self):
        return dict(
            cid=self.cid,
            version=self.version,
            url=self.url,
            title=self.title,
            slug=self.slug,
            permanent_url=self.permanent_url,
            headline=self.headline,
            thumbnail=self.thumbnail,
            category=self.category,
            subcategory=self.subcategory,
            tags=self.tags,
            keywords=self.keywords,
            created=self.created,
            description=self.description,
            requirements_data=self.requirements_data,
            what_you_will_learn_data=self.what_you_will_learn_data,
            who_should_attend_data=self.who_should_attend_data,
            captions=self.captions,
            instructional_level=self.instructional_level,
            content_info=self.content_info,
            faq=self.faq,
            price=self.price
        )

    def export_to_markdown(self):
        content = [
            f"---",
            f"title: {self.title}",
            f"slug: {self.permanent_url}",
            f"category: {self.category}",
            f"author: Real Course Discounts",
            f"tags: {self.tags}",
            f"keywords: {self.keywords}",
            f"date: {self.created}",
            f"thumbnail: {self.thumbnail}",
            f"featured: true",
            f"---",
            f"\nimport ButtonLink from '@components/Mdx/ButtonLink'",
            f"\n{self.headline}",
            f"\n<h2>Description</h2>",
            f"\n{self.description}"
        ]

        if self.requirements_data:
            content.append(f"\n<h2>Requirements Data</h2>")
            li = [f'<li>{item}</li>' for item in self.requirements_data]
            ul = f"<ul>{''.join(li)}</ul>"
            content.append(f"{ul}")

        if self.what_you_will_learn_data:
            content.append(f"\n<h2>What You Will Learn Data?</h2>")
            li = [f'<li>{item}</li>' for item in self.what_you_will_learn_data]
            ul = f"<ul>{''.join(li)}</ul>"
            content.append(f"{ul}")

        if self.who_should_attend_data:
            content.append(f"\n<h2>Who Should Attend Data?</h2>")
            li = [f'<li>{item}</li>' for item in self.who_should_attend_data]
            ul = f"<ul>{''.join(li)}</ul>"
            content.append(f"{ul}")

        if self.captions:
            content.append(f"\n<h2>Captions</h2>")
            li = [f'<li>{item}</li>' for item in self.captions]
            ul = f"<ul>{''.join(li)}</ul>"
            content.append(f"{ul}")

        faq = [f"<strong>{item['question']}</strong><p>{item['answer']}</p>" for item in self.faq]

        content.extend(
            [
                f"\n<h2>Instructional Level</h2>",
                f"{self.instructional_level}",
                f"\n<h2>Content Info</h2>",
                f"{self.content_info}",
                f"\n<h2>FAQ</h2>",
                f"{''.join(faq)}"
            ]
        )

        markdown = [
            html2markdown.convert('\n'.join(content)).replace('&amp', '&').replace('&;', '&'),
            f"\n<ButtonLink to='https://www.udemy.com{self.url}' "
            f"variant='primary' aria-label='Enroll Now'>Enroll Now</ButtonLink>"
        ]

        result = '\n'.join(markdown)
        return result
