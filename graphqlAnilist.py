import requests
import json
import pandas as pd
import datetime
from datetime import timedelta
import urllib.parse
import sqlite3
# import time


def get_data():

    query = """query (
      $page: Int,
      $type: MediaType,
      $status: MediaStatus
      $format: MediaFormat,
      $startDate: String,
      $endDate: String,
      $season: MediaSeason,
      $seasonYear: Int,
      $genres: [String],
      $genresExclude: [String],
      $isAdult: Boolean = false,
      $sort: [MediaSort],
    ) {
      Page (page: $page) {
        media (
          startDate_like: $startDate,
          endDate_like: $endDate,
          season: $season,
          seasonYear: $seasonYear
          type: $type,
          status: $status,
          format: $format,
          genre_in: $genres,
          genre_not_in: $genresExclude,
          isAdult: $isAdult,
          sort: $sort,
        ) {
          title {
            userPreferred
            romaji
            english
          }
          endDate {
            year
            month
            day
          }
          id
          episodes
          averageScore
          popularity
          nextAiringEpisode {
            airingAt
            timeUntilAiring
            episode
          }
          coverImage {
            large
            medium
          }
        }
      }
    }"""

    variables = {
      "page": 1,
      "type": "ANIME",
      "format": "TV",
      "status": "RELEASING",
      "sort": "POPULARITY_DESC"
    }

    url = "https://graphql.anilist.co/"

    r = requests.post(url, json={'query': query, 'variables': variables})

    # print(r.status_code)
    # print(r.text)

    json_data = json.loads(r.text)

    json_data = json_data['data']['Page']['media']

    return json_data


def create_df(scraped_data):

    anime_data = {'title_preferred': [], 'title_fake_eng': [],
                  'title_real_eng': [], 'title1_encoded': [],
                  'title2_encoded': [], 'title3_encoded': [],
                  'end_date': [], 'episodes': [],
                  'cover_large': [], 'cover_medium': [],
                  "anilist_id": []
                  }

    airing_data = {'avg_score': [], 'popularity': [],
                   'cur_episode': [], 'time_until_airing': [],
                   'airing_at': [], 'airing_date': [],
                   'airing_time': [], 'next_airing_at': [],
                   'weekly_key': [], 'foreign_key': []
                   }

    clean_list = list(anime_data.keys())
    title_columns = list(scraped_data[0]['title'].keys())
    headers = ["title1_encoded", "title2_encoded", "title3_encoded"]

    for anime in range(len(scraped_data)):

        if scraped_data[anime]['nextAiringEpisode'] is not None:

            for clean_title, column, header in zip(clean_list[0:3],
                                                   title_columns, headers):

                anime_data[clean_title].\
                  append(scraped_data[anime]['title'][column])

                if scraped_data[anime]['title'][column] is None:

                    anime_data[header].append("empty")

                else:

                    anime_data[header].\
                      append('https://nyaa.si/?f=0&c=1_2&q=' +
                             urllib.parse.quote(str(
                               scraped_data[anime]['title'][column])) +
                             '&s=id&o=desc')

            anime_data['end_date'].append(f"{data[anime]['endDate']['year']}" +
                                          "-" +
                                          f"{data[anime]['endDate']['month']}"
                                          + "-" +
                                          f"{data[anime]['endDate']['day']}")

            if scraped_data[anime]['episodes'] is None:

                anime_data['episodes'].\
                  append(scraped_data[anime]['episodes'])

            else:

                anime_data['episodes'].append(9999)

            anime_data['cover_large'].append(
              scraped_data[anime]['coverImage']['large'].replace("\\", ""))
            anime_data['cover_medium'].append(
              scraped_data[anime]['coverImage']['medium'].replace("\\", ""))

            anime_data['anilist_id'].append(
              scraped_data[anime]['id'])

            airing_data['avg_score'].append(
              scraped_data[anime]['averageScore'])
            airing_data['popularity'].append(
              scraped_data[anime]['popularity'])

            airing_data['cur_episode'].append(
              int(scraped_data[anime]['nextAiringEpisode']['episode']) - 1)

            airing_data['time_until_airing'].append(
              str(datetime.timedelta(
                seconds=int(
                  scraped_data[anime]['nextAiringEpisode']['timeUntilAiring']))
                  ))

            airing_data['airing_at'].append(
              (datetime.datetime.fromtimestamp(
                scraped_data[anime]['nextAiringEpisode']['airingAt'],
                datetime.timezone.utc) - timedelta(days=7)).strftime(
                  '%Y-%m-%d %H:%M:%S'))

            airing_data['airing_date'].append(
              airing_data['airing_at'][-1].split()[0])
            airing_data['airing_time'].append(
              airing_data['airing_at'][-1].split()[1])

            airing_data['next_airing_at'].append(
              datetime.datetime.fromtimestamp(
                scraped_data[anime]['nextAiringEpisode']['airingAt'],
                datetime.timezone.utc).strftime('%Y-%m-%d'))

            airing_data['weekly_key'].append(
              str(scraped_data[anime]['title'][title_columns[0]]) + str(
                airing_data['airing_at'][-1]))

            airing_data['foreign_key'].append(
              len(anime_data['title_preferred']))

    anime_df = pd.DataFrame.from_dict(data=anime_data, orient='columns')

    airing_df = pd.DataFrame.from_dict(data=airing_data, orient='columns')

    anime_df.to_csv("./data_files/anilist_anime.txt")

    # airing_df.to_csv("./app/data_files/anilist_airing.txt")

    return anime_df, airing_df


if __name__ == '__main__':

    # start_time = time.time()

    data = get_data()

    anime_df, airing_df = create_df(data)

    # # print(time.time() - start_time)

    connection = sqlite3.connect('./app/pontansubs.db')

    cursor = connection.cursor()

    dropper = """
            DROP TABLE IF EXISTS AnilistAnime
            """

    anilist_anime = """
                CREATE TABLE IF NOT EXISTS AnilistAnime (
                anime_id INTEGER NOT NULL PRIMARY KEY NULL,
                title_preferred TEXT UNIQUE,
                title_fake_eng TEXT,
                title_real_eng TEXT,
                title1_encoded TEXT,
                title2_encoded TEXT,
                title3_encoded TEXT,
                end_date TEXT,
                episodes INTEGER,
                cover_large TEXT,
                cover_medium TEXT,
                anilist_id INTEGER
                )
                """

    anilist_airing = """
                CREATE TABLE IF NOT EXISTS AnilistAiring (
                airing_id INTEGER NOT NULL PRIMARY KEY,
                avg_score INTEGER,
                popularity INTEGER,
                cur_episode INTEGER,
                time_until_airing TEXT,
                airing_at INTEGER,
                airing_date TEXT,
                airing_time TEXT,
                next_airing_at TEXT,
                weekly_key TEXT UNIQUE,
                foreign_key INTEGER,
                FOREIGN KEY(foreign_key) REFERENCES AnilistAnime(anime_id)
                )
                """

    with connection:

        cursor.execute(dropper)
        cursor.execute(anilist_anime)
        cursor.execute(anilist_airing)

        for index, row in anime_df.iterrows():

            cursor.execute("INSERT OR REPLACE INTO AnilistAnime (title_preferred, \
                            title_fake_eng, title_real_eng, title1_encoded, \
                            title2_encoded, title3_encoded, end_date, \
                            episodes, cover_large, cover_medium, anilist_id)\
                            VALUES (\
                            :title_preferred, :title_fake_eng, \
                            :title_real_eng, :title1_encoded, \
                            :title2_encoded, :title3_encoded, \
                            :end_date, :episodes, \
                            :cover_large, :cover_medium, :anilist_id)",
                           {'title_preferred': row[0],
                            'title_fake_eng': row[1],
                            'title_real_eng': row[2], 'title1_encoded': row[3],
                            'title2_encoded': row[4], 'title3_encoded': row[5],
                            'end_date': row[6], 'episodes': row[7],
                            'cover_large': row[8], 'cover_medium': row[9],
                            'anilist_id': row[10]})

        for index, row in airing_df.iterrows():

            cursor.execute("INSERT OR REPLACE INTO AnilistAiring (\
                            avg_score, popularity, cur_episode, \
                            time_until_airing, airing_at, \
                            airing_date, airing_time, \
                            next_airing_at, weekly_key, foreign_key) VALUES (\
                            :avg_score, :popularity, \
                            :cur_episode, :time_until_airing, \
                            :airing_at, :airing_date, \
                            :airing_time, :next_airing_at, \
                            :weekly_key, :foreign_key)",
                           {'avg_score': row[0], 'popularity': row[1],
                            'cur_episode': row[2], 'time_until_airing': row[3],
                            'airing_at': row[4], 'airing_date': row[5],
                            'airing_time': row[6], 'next_airing_at': row[7],
                            'weekly_key': row[8], 'foreign_key': row[9],
                            })
