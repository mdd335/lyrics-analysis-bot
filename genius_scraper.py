from song import Song

from bs4 import BeautifulSoup
import requests
import re
import asyncio
import aiohttp


class Genius_scraper:

    def __init__(self):

        with open("genius.env", "r") as envfile:
            envfilestring = envfile.read()
            envvariables = envfilestring.split("\n")
            self.apidict = {}
            for var in envvariables:
                split = var.split(":")
                self.apidict[split[0]] = split[1]

        self.base = "https://api.genius.com"

    def get_artist_songs_list(self, artist):
        """Creates and returns a list of song objects with title, year and lyrics for an artist"""
        artist_id = self.get_artist_id(artist)
        song_return_objects = self.get_songs_by_artist(artist_id)

        # Filter: only songs as main artist
        song_return_objects_main_artist = [song for song in song_return_objects if song["primary_artist"]["id"] == artist_id]
        print("Found " + str(len(song_return_objects_main_artist)) + " songs as main artist")
        print()

        # Create url list from song return objects
        url_list = []
        for song in song_return_objects_main_artist:
            url = "http://genius.com" + song["path"]
            url_list.append(url)

        # Create html list from url list
        html_list = self.get_html_list_aio(url_list)

        # Get song data, add song objects to new list if year and lyrics found
        artist_songs_list = []
        for html in html_list:
            title = self.get_song_title(html)
            song = Song(title)
            song.set_year(self.get_song_year(html))
            if song.year is None:
                song.set_year("unknown")
            song.set_lyrics(self.get_song_lyrics(html))

            if song.lyrics is not None:
                artist_songs_list.append(song)

        return artist_songs_list

    def get_artist_id(self, artist_name):
        """Gets the id of an artist from Genius."""
        path ="search"
        params = {'q' : artist_name}
        data = self.get_json(path = path, params = params)
        artist_id = data['response']['hits'][0]['result']['primary_artist']['id']
        print("Artist ID is: {}".format(artist_id))
        return artist_id

    def get_songs_by_artist(self, artist_id):
        """Get all the song ids from an artist."""
        current_page = 1
        next_page = True
        songs = [] # to store final song ids

        while next_page:
            path = "artists/{}/songs/".format(artist_id)
            params = {'page': current_page} # the current page
            data = self.get_json(path=path, params=params) # get json of songs

            page_songs = data['response']['songs']
            if page_songs:
                # Add all the songs of current page
                songs += page_songs
                # Increment current_page value for next loop
                current_page += 1
                print("Page {} finished scraping".format(current_page))

            else:
                # If page_songs is empty, quit
                next_page = False
                print("All pages finished scraping")

        print("Found " + str(len(songs)) + " songs")

        return songs

    def get_html_list_aio(self, url_list):
        html_list = []

        async def get(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as response:
                    resp = await response.read()
                    html_list.append(BeautifulSoup(resp, "html.parser"))
                    print(f'Downloaded html of {url}')

        async def main(urls):
            ret = await asyncio.gather(*[get(url) for url in urls])

        asyncio.run(main(url_list))
        return html_list

    def get_html_list(self, url_list):
        html_list = []

        for url in url_list:
            page = requests.get(url)
            html_list.append(page.text)

        return html_list

    def get_song_title(self, html):
        """Extracts the song title from an html"""
        song_title = html.find("h1", class_="header_with_cover_art-primary_info-title")
        if song_title is None:
            # print("(Title is not in h1 with class header_with_cover_art-primary_info-title)")
            song_title = html.find('h1', class_=re.compile(r'^SongHeader__Title'))
        if song_title is None:
            print()
            print("No title found")
        else:
            song_title_string = song_title.get_text()
            print()
            print("Found title: {}".format(song_title_string))
        return song_title_string

    def get_song_year(self, html):
        """Extracts the release year from an html"""

        release_date_element = html.find("span", string="Release Date")

        if release_date_element is None:
            release_date_element = html.find("p", string="Release Date")

            if release_date_element is not None:
                release_date = release_date_element.next_sibling

        else:
            release_date = release_date_element.next_sibling.next_sibling.get_text()

        # TODO: use album release year alternatively

        if release_date_element is not None:

            if release_date is not None:

                release_year = int(release_date[-4:])

                if release_year > 1799 and release_year < 2100:
                    print("Found year: {}".format(release_year))
                    return release_year

        print("No year found")
        return None

    def get_song_lyrics(self, html):
        """Extracts the lyrics from an html"""
        song_lyrics = html.find("div", class_="lyrics")
        if song_lyrics is None:
            # print("(Lyrics are not in div with class lyrics)")
            song_lyrics = html.find('div', class_=re.compile(r'^Lyrics__Container'))
        if song_lyrics is None:
            print("No lyrics found")
            return None
        else:
            song_lyrics_string = song_lyrics.get_text(" ")
            if song_lyrics_string is None:
                print("No lyrics found")
                return None
            else:
                print("Found lyrics")
                return self.clean_lyrics(song_lyrics_string)

    def clean_lyrics(self, lyrics):
        """Clean lyrics from punctuation, new lines, etc."""

        lyrics = lyrics.replace(".", " ")
        lyrics = lyrics.replace(",", " ")
        lyrics = lyrics.replace(":", " ")
        lyrics = lyrics.replace(";", " ")
        lyrics = lyrics.replace("\n", " ")
        lyrics = lyrics.replace("\u2005", " ")
        lyrics = lyrics.replace("\u205f", " ")
        lyrics = lyrics.replace("(", " ")
        lyrics = lyrics.replace(")", " ")
        lyrics = lyrics.replace("!", " ")
        lyrics = lyrics.replace("?", " ")
        lyrics = lyrics.replace("\"", " ")
        lyrics = lyrics.replace("\'", "")
        lyrics = lyrics.replace("#", " ")

        skip1c = 0
        lyrics_formated = ""
        for i in lyrics:
            if i == '[':
                skip1c += 1
            elif i == ']' and skip1c > 0:
                skip1c -= 1
            elif skip1c == 0:
                lyrics_formated += i

        while '  ' in lyrics_formated:
            lyrics_formated = lyrics_formated.replace('  ', ' ')

        lyrics_formated = lyrics_formated.lower()

        return lyrics_formated

    def get_json(self, path, params=None, headers=None):
        """Send request and get response in json format."""

        # Generate request URL
        requrl = '/'.join([self.base, path])
        token = "Bearer {}".format(self.apidict['clientaccesstoken'])
        if headers:
            headers['Authorization'] = token
        else:
            headers = {"Authorization": token}

        # Get response object from querying genius api
        response = requests.get(url=requrl, params=params, headers=headers)
        response.raise_for_status()
        return response.json()