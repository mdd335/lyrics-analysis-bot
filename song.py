class Song:

    def __init__(self, title):
        self.title = title

    def set_title(self, title):
        self.title = title

    def set_year(self, year):
        self.year = year

    def set_lyrics(self, lyrics):
        self.lyrics = lyrics

    def set_keywords(self, keywords):
        self.keywords = keywords

    def get_title(self):
        return self.title

    def get_year(self):
        return self.year

    def get_lyrics(self):
        return self.lyrics

    def get_keywords(self):
        return self.keywords
