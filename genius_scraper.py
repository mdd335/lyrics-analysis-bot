from song import Song

from bs4 import BeautifulSoup
import requests
import re
import asyncio
import aiohttp
import random


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

    def get_artist_songs_list(self, artist_id, artist_name):
        """Creates and returns a list of song objects with title, year and lyrics for an artist"""

        print(f'Scraping {artist_name}')

        # Get list of songs by artist from Genius
        song_return_objects = self.get_songs_by_artist(artist_id)

        # Filter: only songs as main artist
        song_return_objects_main_artist = [song for song in song_return_objects if song["primary_artist"]["id"] == artist_id]
        print("Found " + str(len(song_return_objects_main_artist)) + " songs as main artist")
        print()

        # If there are more than 900 songs in the list, choose random sample of 900
        if len(song_return_objects_main_artist) > 900:
            print("More than 900 songs, so taking random sample of 900.")
            song_return_objects_main_artist = random.sample(song_return_objects_main_artist, 900)

        # Make url list from song return objects
        artist_songs_list = [Song("http://genius.com" + song["path"]) for song in song_return_objects_main_artist]

        # Add HTMLs to artist_songs_list
        self.add_htmls_to_songs_list(artist_songs_list)
        songs_list_with_html = [song for song in artist_songs_list if song.html is not None]
        print(f"Successfully downloaded {len(songs_list_with_html)} of {len(artist_songs_list)} HTMLs")
        print()

        # Add song data (title, artist, year, lyrics) to artist_songs_list
        self.add_title_artist_year_lyrics_to_songs_list(artist_name, songs_list_with_html)
        print(f'Successfully found year of {len([song for song in artist_songs_list if song.year != "unknown year"])} songs.')
        print()

        # X times, if html download failed or no year found, try again
        for _ in range(3):
            songs_list_no_html_or_no_year = [song for song in artist_songs_list if song.html is None or song.year == "unknown year"]
            self.add_htmls_to_songs_list(songs_list_no_html_or_no_year)
            songs_list_with_html = [song for song in songs_list_no_html_or_no_year if song.html is not None]
            self.add_title_artist_year_lyrics_to_songs_list(artist_name, songs_list_with_html)
            print(f'Successfully downloaded HTML and found year of another {len([song for song in songs_list_no_html_or_no_year if song.year != "unknown year"])} songs.')

        print(f'END: Successfully found year of {len([song for song in artist_songs_list if song.year != "unknown year"])} songs.')

        # Delete HTMLs from song objects
        for song in artist_songs_list:
            song.html = None

        if len(artist_songs_list) < (len(song_return_objects_main_artist) * 0.9):
            return "Error"

        return [song for song in artist_songs_list if song.lyrics is not None]

    def get_artist_name_url_id_of_first_4(self, artist_search_str):
        """Gets the first 4 artists of the search results for a search string (with name, url and id)."""
        path ="search"
        params = {'q' : artist_search_str}
        data = self.get_json(path = path, params = params)

        artist_suggestions = []
        for artist in data['response']['hits']:
            artist_name = artist['result']['primary_artist']['name']
            if not any(artist_name == artist_suggestion['name'] for artist_suggestion in artist_suggestions):
                if not ("," in artist_name and "&" in artist_name):
                    artist_url = artist['result']['primary_artist']['url']
                    artist_id = artist['result']['primary_artist']['id']
                    artist_suggestions.append({"name": artist_name, "url": artist_url, "id": artist_id})

        return artist_suggestions

    def get_artist_name_url_id(self, artist_search_str):
        """Gets the name, url and id of an artist from Genius."""
        path ="search"
        params = {'q' : artist_search_str}
        data = self.get_json(path = path, params = params)
        artist_name = data['response']['hits'][0]['result']['primary_artist']['name']
        artist_url = data['response']['hits'][0]['result']['primary_artist']['url']
        artist_id = data['response']['hits'][0]['result']['primary_artist']['id']
        return artist_name, artist_url, artist_id

    def get_songs_by_artist(self, artist_id):
        """Get all the song ids from an artist."""
        current_page = 1
        next_page = True
        songs = [] # to store final song ids

        print("Scraping pages ...")

        while next_page:
            try:
                path = "artists/{}/songs/".format(artist_id)
                params = {'page': current_page} # the current page
                data = self.get_json(path=path, params=params) # get json of songs

                page_songs = data['response']['songs']
                if page_songs:
                    # Add all the songs of current page
                    songs += page_songs
                    # Increment current_page value for next loop
                    current_page += 1
                    # print("Page {} finished scraping".format(current_page))

                else:
                    # If page_songs is empty, quit
                    next_page = False
                    print("All pages finished scraping")
            except:
                print("Error scraping page {}".format(current_page))

        return songs

    def add_htmls_to_songs_list(self, songs_list):

        print("Downloading HTMLs ...")

        # Create html list from url list,
        # splitting it up if more than 300 songs, because for some reasons aiohttp seems to struggle with bigger lists
        if len(songs_list) > 600:
            self.get_htmls_aio(songs_list[:299])
            self.get_htmls_aio(songs_list[300:599])
            self.get_htmls_aio(songs_list[600:])
        elif len(songs_list) > 300:
            self.get_htmls_aio(songs_list[:299])
            self.get_htmls_aio(songs_list[300:])
        else:
            self.get_htmls_aio(songs_list)

    def get_htmls_aio(self, songs_list):

        async def get(song):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=song.url) as response:
                        resp = await response.read()
                        song.html = BeautifulSoup(resp, "html.parser")
                        # print(f'Downloaded html of {song.url}')
            except:
                print(f'Error downloading html of {song.url}')

        async def main(songs):
            ret = await asyncio.gather(*[get(song) for song in songs])

        asyncio.run(main(songs_list))

    def get_htmls(self, url_list):
        html_list = []

        for url in url_list:
            page = requests.get(url)
            html_list.append(BeautifulSoup(page.text, "html.parser"))
            print(f'Downloaded html of {url}')

        return html_list

    def add_title_artist_year_lyrics_to_songs_list(self, artist_name, artist_songs_list):
        print("Adding title, artist, year, lyrics ...")
        for song in artist_songs_list:
            song.title = self.get_song_title(song.html)
            song.artist = artist_name
            song.year = self.get_song_year(song.html)
            song.lyrics = self.get_song_lyrics(song.html)

    def get_song_title(self, html):
        """Extracts the song title from an html"""
        song_title = html.find("h1", class_="header_with_cover_art-primary_info-title")
        if song_title is None:
            # print("(Title is not in h1 with class header_with_cover_art-primary_info-title)")
            song_title = html.find('h1', class_=re.compile(r'^SongHeader__Title'))
        if song_title is None:
            # print("No title found, ", end='')
            return "unknown title"
        else:
            song_title_string = song_title.get_text()
            # print("Found title: {}, ".format(song_title_string), end='')
        return song_title_string

    def get_song_year(self, html):
        try:
            # Try to find release date in span
            release_date_element = html.find("span", string="Release Date")
            release_date = release_date_element.next_sibling.next_sibling.get_text()
            release_year = int(release_date[-4:])

        except:
            try:
                # Try to find in p
                release_date_element = html.find("p", string="Release Date")
                release_date = release_date_element.next_sibling
                release_year = int(release_date[-4:])

            except:
                try:
                    # No release date found, so look for album release year
                    album_release_year_element = html.find("span", class_="song_album-info-release_year")
                    release_date = album_release_year_element.get_text()
                    release_year = int(release_date[-5:-1])

                except:
                    try:
                        release_date_element = html.select("a[class^=PrimaryAlbum__Title]")
                        release_year = release_date_element[0].get_text()[-5:-1]
                    except:
                        # TODO: make year finder even better
                        # print("No year found, ", end='')
                        return "unknown year"

        if release_year is not None:
            try:
                release_year_int = int(release_year)
                if 1600 < release_year_int < 2100:
                    # print(f"Found year: {release_year}, ", end='')
                    return release_year_int
            except:
                # print("No year found, ", end='')
                return "unknown year"

    def get_song_lyrics(self, html):
        """Extracts the lyrics from an html"""

        try:
            song_lyrics_element = html.find("div", class_="lyrics")
            song_lyrics_string = song_lyrics_element.get_text(" ")
        except:
            try:
                song_lyrics_elements = html.find_all('div', class_=re.compile(r'^Lyrics__Container'))
                song_lyrics_string = ""
                for elem in song_lyrics_elements:
                    song_lyrics_string += elem.get_text(" ")
            except:
                return None

        '''
        if len(song_lyrics_string) < 20:
            print("Unrealistically short lyrics found")
            return None
        '''

        if song_lyrics_string is None:
            # print("No lyrics found")
            return None
        else:
            # print("Found lyrics")
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