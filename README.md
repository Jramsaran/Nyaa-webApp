# Nyaa-webApp

[Link to the website](https://www.pontansubs.cc)

This site gathers newly released fansub episodes of seasonal anime on Nyaa.si. I decided to make this website because HorribleSubs shut down due to Covid issues. Me and many others frequently used this website to find and download seasonal anime. Nyaa delivers fansubs but finding newly released episode takes significantly more effort than the effort it took on HorribleSubs. So I made this episode to display the new releases on Nyaa in a more convenient overview, similar to the one that HorribleSubs used. This was a wonderful project to work on and I was extremely satisfied by the result. I hope others also find joy browsing this site and find this site a suitable alternative to HorribleSubs.

I plan to add additional features to this web app in the feature, such as a filter by name and by video quality. 

### Web scrapers

###### graphqlAnilist

This webscraper uses the Anilist GraphQL API to gather the data of anime that are currently airing. Using this data, links are programatically generated that will be used by the next webscraper. The dataframe is made using Pandas and is stored in an SQLite database.

###### Nyaa_scraper

This webscraper uses Scrapy to scrape Nyaa.si for the links that were generated by *graphqlAnilist* and searches for all the newly released fansubs on this website. This data is also stored in the SQLite database.

### front end

###### index.html

The front-end of the website is made using html, css and a bit of javascript. Materializecss is used for most of the widgets. Placeholders are put in place to programatically fill the webpage with newly gathered data from the webscrapers.

### flask web app

###### app.py

Using Flask, *run.py* runs the *app* package and uses the data gathered from the previous webscrapers. Using object-relational mapping, this app combines the data from multiple tables to generate the contents of the web page. The app then renders *index.html*, and fills the placeholders with the data gathered by the SQL queries. The webpage display the newly released fansubs per anime, as soon as they get released. The added value of this website is that it displays the releases of all seasonal anime and it also shows the new releases conveniently per anime. It also displays a schedule of all anime airing today. 
