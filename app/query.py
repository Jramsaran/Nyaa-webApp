from sqlalchemy.ext.automap import automap_base
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from app import app


db = SQLAlchemy(app)

Base = automap_base()
Base.prepare(db.engine, reflect=True)

AnilistAnime = Base.classes.AnilistAnime
AnilistAiring = Base.classes.AnilistAiring
Nyaa = Base.classes.Nyaa


class Query:

    def final_episode(self):

        final_ep_query = db.session.query(AnilistAnime, AnilistAiring).\
            filter(AnilistAnime.anime_id == AnilistAiring.foreign_key,
                   AnilistAnime.episodes == (AnilistAiring.cur_episode + 1),
                   AnilistAiring.next_airing_at >= datetime.utcnow().date())

        for c, i in final_ep_query:

            final_ep = AnilistAiring(avg_score=i.avg_score,
                                     popularity=i.popularity,
                                     cur_episode=c.episodes,
                                     time_until_airing="FINISHED",
                                     airing_at=i.next_airing_at,
                                     airing_date=i.next_airing_at.split()[0],
                                     airing_time=i.next_airing_at.split()[-1],
                                     next_airing_at="2040-01-01",
                                     weekly_key=c.title_preferred +
                                     i.airing_date,
                                     foreign_key=c.anime_id)

            db.session.add(final_ep)
            db.session.commit()

    def header_names(self):

        headers = []

        headers.append("Today")
        headers.append("Yesterday")

        for day in range(2, 7):

            headers.append((datetime.utcnow().date() - timedelta(days=day)).
                           strftime('%A'))

        return headers

    def get_pics(self, amount):

        pics = []
        week_ago = (datetime.utcnow() - timedelta(days=7)).\
            strftime('%Y-%m-%d %H:%M:%S')

        image_query = db.session.query(AnilistAnime, AnilistAiring).\
            filter(AnilistAnime.anime_id == AnilistAiring.foreign_key,
                   AnilistAiring.airing_at >= week_ago,
                   AnilistAiring.cur_episode <= 13).\
            order_by(AnilistAiring.popularity.desc()).limit(amount).all()

        for output, airing in image_query:
            pics.append([output.cover_large, "https://anilist.co/anime/" +
                         f"{output.anilist_id}"])

        return pics

    def pop_outs(self):

        anime_names = {}

        headers = self.header_names()

        qualities = ["1080p", "720p", "480p"]

        for header, day in zip(headers, range(7)):

            anime_names[header] = {}

            anime_query = db.session.query(AnilistAnime, AnilistAiring, Nyaa).\
                filter(AnilistAnime.anime_id == AnilistAiring.foreign_key,
                       AnilistAnime.anime_id == Nyaa.foreign_key,
                       AnilistAiring.airing_date >= (datetime.utcnow() -
                                                     timedelta(days=(day+1))),
                       AnilistAiring.airing_date <= (datetime.utcnow() -
                                                     timedelta(days=day)),
                       Nyaa.upload_date >= (datetime.utcnow() -
                                            timedelta(days=7)),
                       Nyaa.quality.in_(qualities)).\
                order_by(AnilistAiring.airing_at.desc()).all()

            for c, i, d in anime_query:
                # Delete entries where time until airing is longer than a week

                if "," in i.time_until_airing and int(i.time_until_airing.
                                                      split()[0]) > 7:

                    deleted_object1 = AnilistAnime.__table__.delete().\
                                      where(AnilistAnime.anime_id ==
                                            c.anime_id)
                    deleted_object2 = AnilistAiring.__table__.delete().\
                        where(AnilistAiring.weekly_key == i.weekly_key)
                    db.session.execute(deleted_object1)
                    db.session.execute(deleted_object2)
                    db.session.commit()

                if i.airing_date == (datetime.utcnow() - timedelta(days=day)).\
                        date().strftime('%Y-%m-%d'):

                    key_list = [f"{c.title_preferred} " +
                                "Episode " + f"{i.cur_episode}",
                                "Anime rating: " +
                                f"{i.avg_score}"]

                    key = tuple(key_list)

                    if key not in anime_names[header].keys():

                        anime_names[header][key] = []

                    anime_names[header][key].append([d.episode_name,
                                                     "https://nyaa.si" +
                                                     d.episode_link,
                                                     d.magnet_link,
                                                     d.torrent_size,
                                                     d.upload_date, d.seeders,
                                                     d.leechers,
                                                     d.download_amount])

                if not anime_names[header]:

                    anime_names[header][0] = "No releases on this day"

        return anime_names

    def no_new_anime(self, pop_outs_result):

        for key in pop_outs_result.keys():

            if not pop_outs_result[key]:

                pop_outs_result[key][tuple(["No new anime released yet today.",
                                            ""])] = []

    def schedule(self):

        schedule = []

        schedule_query = db.session.query(AnilistAnime, AnilistAiring).\
            filter(AnilistAnime.anime_id == AnilistAiring.foreign_key,
                   AnilistAiring.next_airing_at == datetime.utcnow().date()). \
            order_by(AnilistAiring.airing_at.asc()).all()

        for c, i in schedule_query:

            if datetime.strptime((f"{i.next_airing_at} " + f"{i.airing_time}"),
                                 '%Y-%m-%d %H:%M:%S') < datetime.utcnow():

                aired = str(datetime.utcnow() -
                            datetime.strptime((f"{i.next_airing_at} " +
                                               f"{i.airing_time}"),
                                              '%Y-%m-%d %H:%M:%S')).split(":")

                if "0" in aired[0][0]:

                    aired[0] = aired[0][-1]

                if "0" in aired[1][0]:

                    aired[1] = aired[1][-1]

                status = "Aired " + f"{aired[0]} " + "hour(s) ago and " + \
                         f"{aired[1]} " + "minute(s) ago"

            else:

                airing = i.time_until_airing.split(":")

                if "0" in airing[1][0]:

                    airing[1] = airing[1][-1]

                status = "Airing in " + f"{airing[0]} " + "hours and " + \
                         f"{airing[1]} " + "minutes"

            schedule.append([c.cover_medium, c.title_preferred,
                             status,
                             "https://anilist.co/anime/" + f"{c.anilist_id}"])

        return schedule
