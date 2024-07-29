import scrapy
import datetime
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags

class Article(scrapy.Item):
    url = scrapy.Field()  # URL of the article
    title = scrapy.Field()  # Title of the article
    text = scrapy.Field()  # Text of the article
    access_date = scrapy.Field()  # Date when the article was accessed
    creation_date = scrapy.Field()  # Date when the article was created
    category = scrapy.Field()  # Category of the article

class ArticleLoader(ItemLoader):
    """A custom Scrapy ItemLoader for loading information about an article."""

    # Use the TakeFirst output processor as the default output processor
    default_output_processor = TakeFirst()

    # Define the input and output processors for the title field
    title_in = MapCompose(remove_tags, str.strip)
    title_out = TakeFirst()

    # Define the input and output processors for the text field
    text_in = MapCompose(remove_tags, str.strip)
    text_out = Join('\n')


class ItParkSpider(scrapy.Spider):
    name = 'it-park'
    page_no= 0    
    
    writing_systems = {
        'lat': 'uz/',
        'eng': 'en/',
        'rus': 'ru/'
    }

    def __init__(self, ws='lat', **kwargs):
        self.ws = ws
        self.start_urls = [f'https://it-park.uz/{self.writing_systems[self.ws]}itpark/news']
        super().__init__(**kwargs)

    def parse(self, response):
        news_links = response.css('a.article-card::attr(href)').getall()
        yield from response.follow_all(news_links, self.parse_item)

        self.page_no += 1
        yield from response.follow_all([f'{self.start_urls[0]}?page={self.page_no}'], self.parse)

    def parse_item(self, response):
        a = ArticleLoader(item=Article(), response=response)
        a.add_value('url', response.url)
        a.add_css('title', 'h5.alt-font.font-weight-600::text')
        a.add_xpath('text', '//div[contains(@class, "news-show")]//text()')
        a.add_css('creation_date', 'div.text-right p::text')
        a.add_value('access_date', datetime.datetime.now())
        a.add_value('category', 'technology')

        yield a.load_item()
