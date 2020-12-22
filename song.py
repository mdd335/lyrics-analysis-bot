class Song:

    def __init__(self, id):
        self.id = id
        self.title = ""

    def set_title(self, title):
        self.title = title

    def set_year(self, year):
        self.year = year

    def set_lyrics(self, lyrics):
        self.lyrics = lyrics

    def get_id(self):
        return self.id

    def get_title(self):
        return self.title

    def get_year(self):
        return self.year

    def get_lyrics(self):
        return self.lyrics
