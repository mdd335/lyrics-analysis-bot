from bs4 import BeautifulSoup
import requests
import re

with open("genius.env", "r") as envfile:
    envfilestring = envfile.read()
    envvariables = envfilestring.split("\n")
    apidict = {}
    for var in envvariables:
        split = var.split(":")
        apidict[split[0]] = split[1]

base = "https://api.genius.com"


def get_json(path, params=None, headers=None):
    """Send request and get response in json format."""

    # Generate request URL
    requrl = '/'.join([base, path])
    token = "Bearer {}".format(apidict['clientaccesstoken'])
    if headers:
        headers['Authorization'] = token
    else:
        headers = {"Authorization": token}

    # Get response object from querying genius api
    response = requests.get(url=requrl, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_artist_id(artist_name):
    path ="search"
    params = {'q' : artist_name}
    data = get_json(path = path, params = params)
    artist_id = data['response']['hits'][0]['result']['primary_artist']['id']
    print("Artist ID is: {}".format(artist_id))
    return artist_id


def get_song_id(artist_id):
    """Get all the song ids from an artist."""
    current_page = 1
    next_page = True
    songs = [] # to store final song ids

    while next_page:
        path = "artists/{}/songs/".format(artist_id)
        params = {'page': current_page} # the current page
        data = get_json(path=path, params=params) # get json of songs

        page_songs = data['response']['songs']
        if page_songs:
            # Add all the songs of current page
            songs += page_songs
            # Increment current_page value for next loop
            current_page += 1
            print("Page {} finished scraping".format(current_page))
            # If you don't wanna wait too long to scrape, un-comment this
            # if current_page == 2:
            #    break

        else:
            # If page_songs is empty, quit
            next_page = False
            print("All pages finished scraping")
            print(" ")

    print("Found {} songs:".format(len(songs)))
    print(songs)

    return songs


def retrieve_lyrics(song_id):
    """Retrieves lyrics from html page."""

    path = connect_lyrics(song_id)
    URL = "http://genius.com" + path
    page = requests.get(URL)

    print(URL)

    # Extract the page's HTML as a string
    html = BeautifulSoup(page.text, "html.parser")

    song_title = get_song_title(html)

    song_year = get_song_year(html)

    if song_year is not None:
        if song_year > 1799 and song_year < 2100:
            # Realistic year found, so we continue

            song_lyrics = clean_lyrics(get_song_lyrics(html))

            # Return dictionary with song data
            return {"Title": song_title, "Year": song_year, "Lyrics": song_lyrics}

    # No realistic year found, so we return an empty dictionary
    print("")
    return "no year found"


def get_song_lyrics(html):
    # Scrape the song lyrics from the HTML
    song_lyrics = html.find("div", class_="lyrics")
    if song_lyrics is None:
        # print("(Lyrics are not in div with class lyrics)")
        song_lyrics = html.find('div', class_=re.compile(r'^Lyrics__Container'))
    if song_lyrics is None:
        print("No lyrics found")
    else:
        print("Found lyrics")
        song_lyrics_string = song_lyrics.get_text(" ")
    print("")
    return song_lyrics_string


def get_song_year(html):
    # Scrape the song year from the HTML
    # song_year = html.find("span", class_="metadata_unit-info metadata_unit-info--text_only")

    release_date_element = html.find("span", string="Release Date")

    if release_date_element is None:
        release_date_element = html.find("p", string="Release Date")

        if release_date_element is not None:
            release_date = release_date_element.next_sibling

    else:
        release_date = release_date_element.next_sibling.next_sibling.get_text()

    if release_date_element is not None:

        if release_date is not None:
            print("Found year: {}".format(int(release_date[-4:])))
            return int(release_date[-4:])

    print("No year found")
    return None


def get_song_title(html):
    # Scrape the song title from the HTML
    song_title = html.find("h1", class_="header_with_cover_art-primary_info-title")
    if song_title is None:
        # print("(Title is not in h1 with class header_with_cover_art-primary_info-title)")
        song_title = html.find('h1', class_=re.compile(r'^SongHeader__Title'))
    if song_title is None:
        print("No title found")
    else:
        song_title_string = song_title.get_text()
        print("Found title: {}".format(song_title_string))
    return song_title_string


def connect_lyrics(song_id):
    """Constructs the path of song lyrics."""
    url = "songs/{}".format(song_id)
    data = get_json(url)

    # Gets the path of song lyrics
    path = data['response']['song']['path']

    return path


def clean_lyrics(lyrics):
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