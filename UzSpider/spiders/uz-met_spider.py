import scrapy
import datetime
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import re

class Article(scrapy.Item):
    url = scrapy.Field()  # URL of the article
    title = scrapy.Field()  # Title of the article
    text = scrapy.Field()  # Text of the article
    access_date = scrapy.Field()  # Date when the article was accessed
    creation_date = scrapy.Field()  # Date when the article was created

def clean_text(text):
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = text.replace('Facebook', '').replace('Instagram', '').replace('YouTube', '').replace('Telegram', '').replace('Twitter', '').replace('Email', '')
    text = re.sub(r'\n+', '\n', text)  
    text = text.strip()  
    return text

class ArticleLoader(ItemLoader):
    default_output_processor = TakeFirst()

    title_in = MapCompose(remove_tags, str.strip)
    title_out = TakeFirst()

    text_in = MapCompose(remove_tags, str.strip, clean_text)
    text_out = Join('\n')


class ItParkSpider(scrapy.Spider):
    name = 'uz-met'
    page_no= 0    
    
    writing_systems = {
        'kir': 'uz/',
        'lat': 'oz/',
        'eng': 'en/',
        'rus': 'ru/'
    }

    def __init__(self, ws='rus', **kwargs):
        self.ws = ws
        self.start_urls = [f'https://www.uzbekistonmet.uz/{self.writing_systems[self.ws]}lists/category/2']
        super().__init__(**kwargs)

    def parse(self, response):
        news_links = response.css('div.news_box a::attr(href)').getall()
        yield from response.follow_all(news_links, self.parse_item)

        self.page_no += 1
        yield from response.follow_all([f'{self.start_urls[0]}?page={self.page_no}'], self.parse)

    def parse_item(self, response):
        a = ArticleLoader(item=Article(), response=response)
        a.add_value('url', response.url)
        a.add_css('title', 'div.title_in::text')
        a.add_xpath('text', '//div[contains(@class, "news_text")]/p//text()')
        a.add_css('creation_date', 'ul.date_time li:first-child::text')
        a.add_value('access_date', datetime.datetime.now())

        yield a.load_item()
