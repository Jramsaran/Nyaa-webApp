from flask import render_template
from app.query import Query
from app import app


@app.route('/')
def index():

    offsets_1 = ["'col s3 m3 l3 offset-l2 offset-m2 offset-s2'",
                 "'col s3 m3 l3'",
                 "'col s1 m1 l1'"]

    quality = ["1080p", "720p", "480p"]

    a = Query()
    headers = a.header_names()
    pics = a.get_pics(10)
    anime_names = a.pop_outs()
    a.no_new_anime(anime_names)
    schedule = a.schedule()

    return render_template('index.html', pics=pics, offsets_1=offsets_1,
                           quality=quality, headers=headers,
                           anime_names=anime_names,
                           schedule=schedule)
