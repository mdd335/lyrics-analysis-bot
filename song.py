class Song:

    # def __init__(self, artist, title):
    def __init__(self, url):

        self.url = url

        self.html = None

        # self.artist = artist
        self.artist = None

        # self.title = title
        self.title = None

        self.year = None

        self.lyrics = None

        self.keywords = {}
