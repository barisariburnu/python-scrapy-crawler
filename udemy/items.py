#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import scrapy
import random
import requests
import html2markdown
from udemy import settings
from slugify import slugify
from datetime import datetime
from udemy.user_agents import USER_AGENT_LIST


class UdemyItem(scrapy.Item):
    cid = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    slug = scrapy.Field()
    permanent_url = scrapy.Field()
    headline = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    tags = scrapy.Field()
    image_url = scrapy.Field()
    keywords = scrapy.Field()
    created = scrapy.Field()
    requirements_data = scrapy.Field()
    what_you_will_learn_data = scrapy.Field()
    who_should_attend_data = scrapy.Field()
    captions = scrapy.Field()
    instructional_level = scrapy.Field()
    content_info = scrapy.Field()
    faq = scrapy.Field()
    price = scrapy.Field()
    shorten_url = scrapy.Field()
    coupon_code = scrapy.Field()


class UdemyItemParser(object):
    def __init__(self, response):
        self.response = response
        self.__shortened_url = None

    @property
    def cid(self):
        result = str(self.response['id'])
        return result

    @property
    def url(self):
        result = self.response['url']
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
    def tags(self):
        result = [
            f'#freecoursediscounts',
            f'#udemy',
            f'#{slugify(self.category, to_lower=True)}'
        ]

        if self.subcategory:
            result.append(f'#{slugify(self.subcategory, to_lower=True)}')

        return result

    @property
    def keywords(self):
        result = [
            f'Free Course Discounts',
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
    def shorten_url(self):
        if not self.__shortened_url:
            user_agent = random.choice(USER_AGENT_LIST)
            headers = {'user_agent': user_agent, 'public-api-token': settings.SHORTEST_TOKEN}
            data = dict(urlToShorten=f'https://udemy.com{self.url}')
            response = requests.put(settings.SHORTEST_API_URL, data, headers=headers, verify=False)
            shortened_url = json.loads(response.content)
            self.__shortened_url = shortened_url['shortenedUrl']
        return self.__shortened_url

    @property
    def coupon_code(self):
        return 'FreeCourseDiscounts' if self.price == 'Free' else None

    @property
    def absolute_path(self):
        return os.path.join(settings.DATA_PATH, f"{slugify(self.category.replace('&', 'and').lower())}", self.cid)

    def download_thumbnail(self):
        path = os.path.join(self.absolute_path, f'{self.slug}.jpg')
        with open(path, "wb") as f:
            data = requests.get(self.image_url)
            f.write(data.content)

    def save_to_mdx(self):
        path = os.path.join(self.absolute_path, f'{self.slug}.mdx')
        with open(path, "w", encoding='utf8') as f:
            data = self.export_to_markdown()
            f.write(data)

    def export_to_json(self):
        return dict(
            cid=self.cid,
            url=self.url,
            title=self.title,
            slug=self.slug,
            permanent_url=self.permanent_url,
            headline=self.headline,
            image_url=self.image_url,
            thumbnail=f'{self.slug}.jpg',
            category=self.category,
            subcategory=self.subcategory,
            tags=self.tags,
            keywords=self.keywords,
            created=self.created,
            requirements_data=self.requirements_data,
            what_you_will_learn_data=self.what_you_will_learn_data,
            who_should_attend_data=self.who_should_attend_data,
            captions=self.captions,
            instructional_level=self.instructional_level,
            content_info=self.content_info,
            faq=self.faq,
            price=self.price,
            shorten_url=self.shorten_url,
            coupon_code=self.coupon_code
        )

    def export_to_markdown(self):
        content = [
            f"---",
            f"title: '{self.title}'",
            f"slug: {self.permanent_url}",
            f"category: {self.category}",
            f"author: Free Course Discounts",
            f"tags: {self.tags}",
            f"keywords: {self.keywords}",
            f"date: {self.created}",
            f"thumbnail: {self.slug}.jpg",
            f"featured: true",
            f"---",
            f"\nimport ButtonLink from '@components/Mdx/ButtonLink'",
            f"\n{self.headline}"
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
            f"\n<ButtonLink href='{self.shorten_url}' variant='primary' aria-label='Enroll Now'>Enroll Now</ButtonLink>"
        ]

        result = '\n'.join(markdown)
        return result
