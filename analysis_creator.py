from data_analyzer import Data_analyzer
from genius_scraper import Genius_scraper

from tabulate import tabulate
import csv
import io


class Analysis_creator:

    def __init__(self):
        self.test = "test"

    def analyze_artist(self, artist, artist_songs_list, keywords, year_range):

        # Check whether song list has to be scraped
        if artist_songs_list is None:
            # Get songs from Genius
            my_genius_scraper = Genius_scraper()
            artist_songs_list = my_genius_scraper.get_artist_songs_list(artist)
            print()
            print("Found lyrics of " + str(len(artist_songs_list)) + " songs by artist:")
        else:
            # Take songs from artist_dictionary
            print()
            print("Song list taken from artist_dictionary")

        # Make list of song titles
        song_titles = []
        for song in artist_songs_list:
            song_titles.append(song.title)
        print(song_titles)

        # Filter: Only songs with year in year range
        artist_songs_list_filtered = []
        for song in artist_songs_list:
            if song.year in year_range:
                artist_songs_list_filtered.append(song)

        # Get data analysis - percentages by year
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.one_artist_several_keywords(artist_songs_list_filtered, year_range, keywords)
        print("Percentages:")
        print(data_list)

        # Make example sentence
        example_string = f'Example: In {year_range[0]}, {str(data_list[0].get("n containing " + keywords[0]))} of the {data_list[0].get("n total")} songs by {artist} contained the word {keywords[0]}. That is {data_list[0].get("% containing " + keywords[0])} %.'

        # Make and name CSV file
        csv_file = self.make_csv(data_list)
        keywords_string = ' '.join([elem for elem in keywords])
        csv_file.name = f'Lyrics analysis {artist} {str(year_range[0])} - {str(year_range[-1])} {keywords_string}.csv'

        return csv_file, example_string, artist_songs_list

        ''' # Make and print table
        data_for_table = []
        for year in data_list:
            year_data = {"Year": year.get("Year"), "n total": year.get("n total")}
            for keyword in year.get("Keyword data"):
                keyword_string = keyword.get("Keyword")
                year_data["% containing " + keyword_string] = keyword.get("%")
                year_data["n containing " + keyword_string] = keyword.get("n")
            data_for_table.append(year_data)
        output = tabulate(data_for_table, headers="keys")
        print(output)
        print("Example: In " + str(data_list[0].get("Year")) + ", " + str(data_list[0].get("Keyword data")[0].get("n")) + " of the " + str(data_list[0].get("n total")) + " songs by " + artist + " contain the word " + keywords[0] + ". That is " + str(data_list[0].get("Keyword data")[0].get("%")) + " %.")
        '''

    def make_csv(self, data_list):

        # Make 2D list
        list_for_csv = [list(data_list[0].keys())]
        for year in data_list:
            list_for_csv.append(list(year.values()))
        # TODO: Write list of titles of used songs in csv

        # Make CSV
        s = io.StringIO()  # csv module can write data in io.StringIO buffer only
        csv.writer(s).writerows(list_for_csv)
        s.seek(0)
        csv_file = io.BytesIO()  # python-telegram-bot library can send files only from io.BytesIO buffer, so we need to convert StringIO to BytesIO
        csv_file.write(s.getvalue().encode())  # extract csv-string, convert it to bytes and write to buffer
        csv_file.seek(0)

        # TODO: Diagrams

        return csv_file
