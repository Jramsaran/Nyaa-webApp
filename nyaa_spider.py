import scrapy
from scrapy.crawler import CrawlerProcess
from items import NyaaItem
import pandas as pd
import sqlite3
import os
import re


def url_dict(data):

    col_list = ["title1_encoded", "title2_encoded", "title3_encoded"]

    link_dict = {}

    with open(data) as data_file:

        encoded_urls = pd.read_csv(data_file, usecols=col_list)

    df = pd.DataFrame(data=encoded_urls)

    for index, row in df.iterrows():

        link_dict[index] = []

        for column in col_list:

            if row[column] != "empty":

                link_dict[index].append(row[column])

            if column == col_list[-1]:

                link_dict[index] = sorted(set(link_dict[index]))

    return link_dict


class NyaaSpiderSpider(scrapy.Spider):

    name = 'nyaa'

    custom_settings = {

        'DOWNLOAD_DELAY': 1,

        'FEEDS': {'./data_files/nyaa.json': {'format': 'json'}}

        }

    def start_requests(self):

        start_urls = url_dict("./data_files/anilist_anime.txt")

        for key in start_urls.keys():

            for index, value in enumerate(start_urls[key]):

                yield scrapy.Request(url=start_urls[key][index],
                                     callback=self.parse)

    def parse(self, response):

        items = NyaaItem()

        episode_name = response.css('td:nth-child(2) a::attr(title)').extract()
        episode_link = response.css('td:nth-child(2) a::attr(href)').extract()
        magnet_link = response.css('.text-center a+ a::attr(href)').extract()
        torrent_size = response.css('td:nth-child(4)').css('::text').extract()
        upload_date = response.css('td:nth-child(5)').css('::text').extract()
        seeders = response.css('td:nth-child(6)').css('::text').extract()
        leechers = response.css('td:nth-child(7)').css('::text').extract()
        download_amount = response.css('td:nth-child(8)').css('::text').\
            extract()

        items['episode_name'] = episode_name
        items['episode_link'] = episode_link
        items['magnet_link'] = magnet_link
        items['torrent_size'] = torrent_size
        items['upload_date'] = upload_date
        items['seeders'] = seeders
        items['leechers'] = leechers
        items['download_amount'] = download_amount

        yield items


class CleanData(NyaaSpiderSpider):

    def clean_scraped_data(self, data_file):

        with open(data_file) as json_file:

            CleanData.nyaa = pd.read_json(json_file)

        for index, row in CleanData.nyaa.iterrows():

            CleanData.nyaa["episode_name"][index] = \
                    [episode_name for episode_name in
                     CleanData.nyaa["episode_name"][index] if 'comment'
                     not in episode_name]

            CleanData.nyaa["episode_link"][index] = \
                [episode_link for episode_link in
                 CleanData.nyaa["episode_link"][index] if '#comments'
                 not in episode_link]

    def add_foreign_keys(self):

        start_urls = url_dict("./data_files/anilist_anime.txt")

        foreign_key = []

        for key in start_urls.keys():

            for primary_key in start_urls[key]:

                foreign_key.append(key + 1)

        CleanData.nyaa['foreign_key'] = foreign_key

    def unpack_rows(self):

        CleanData.nyaa = CleanData.nyaa.set_index(['foreign_key']).\
            apply(pd.Series.explode).reset_index()

    def quality_column(self):

        quality = []

        for name in CleanData.nyaa['episode_name']:

            search_resolution = re.findall(r"(\d{3,4}[p,P])|\
                                            (\d{3,4}[x,X]\d{3,4})", str(name))

            if len(search_resolution) == 0:

                quality.append("empty")

            if len(search_resolution) > 1:

                search_resolution = [search_resolution[0]]

            for result in search_resolution:

                if not result[0]:

                    quality.append((result[1].lower().split("x")[1]) + "p")

                quality.append(result[0])

        # remove empty strings from list
        quality = [x for x in quality if x]

        CleanData.nyaa['quality'] = quality

        CleanData.nyaa = CleanData.nyaa[['episode_name', 'episode_link',
                                         'magnet_link', 'torrent_size',
                                         'upload_date', 'seeders',
                                         'leechers', 'download_amount',
                                         'quality', 'foreign_key']]


if __name__ == '__main__':

    process = CrawlerProcess()
    process.crawl(NyaaSpiderSpider)
    process.start()

    a = CleanData()

    a.clean_scraped_data('./data_files/nyaa.json')
    a.add_foreign_keys()
    a.unpack_rows()
    a.quality_column()

    connection = sqlite3.connect('./app/pontansubs.db')

    cursor = connection.cursor()

    nyaa = """
                CREATE TABLE IF NOT EXISTS Nyaa (
                torrent_id INTEGER PRIMARY KEY,
                episode_name TEXT NOT NULL,
                episode_link TEXT UNIQUE,
                magnet_link TEXT,
                torrent_size TEXT,
                upload_date TEXT,
                seeders INTEGER,
                leechers INTEGER,
                download_amount INTEGER,
                quality TEXT,
                foreign_key INTEGER,
                FOREIGN KEY(foreign_key) REFERENCES AnilistAnime(anime_id)
                )
                """
    with connection:

        cursor.execute(nyaa)

        for index, row in CleanData.nyaa.iterrows():

            cursor.execute("INSERT OR IGNORE INTO Nyaa (episode_name, \
                            episode_link, magnet_link, torrent_size, \
                            upload_date, seeders, leechers, \
                            download_amount, quality, foreign_key) VALUES (\
                            :episode_name, :episode_link, \
                            :magnet_link, :torrent_size, \
                            :upload_date, :seeders, \
                            :leechers, :download_amount, \
                            :quality, :foreign_key)",
                           {'episode_name': row[0], 'episode_link': row[1],
                            'magnet_link': row[2], 'torrent_size': row[3],
                            'upload_date': row[4], 'seeders': row[5],
                            'leechers': row[6], 'download_amount': row[7],
                            'quality': row[8], 'foreign_key': row[9],
                            })

    # CleanData.nyaa.to_csv("./data_files/nyaa.txt")

    if os.path.exists('./data_files/nyaa.json'):

        os.remove('./data_files/nyaa.json')
