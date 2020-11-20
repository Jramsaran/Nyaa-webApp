import scrapy


class NyaaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    episode_name = scrapy.Field()
    episode_link = scrapy.Field()
    magnet_link = scrapy.Field()
    torrent_size = scrapy.Field()
    upload_date = scrapy.Field()
    seeders = scrapy.Field()
    leechers = scrapy.Field()
    download_amount = scrapy.Field()
