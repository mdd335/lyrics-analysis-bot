from data_analyzer import Data_analyzer
from genius_scraper import Genius_scraper

from tabulate import tabulate
import csv
import io


class Analysis_creator:

    def __init__(self):
        self.test = "test"

    def analyze_artist(self, artist, keywords, years):

        # Get songs from Genius
        my_genius_scraper = Genius_scraper()
        songs = my_genius_scraper.get_song_list(artist, years)
        print()
        print("Found year and lyrics of " + str(len(songs)) + " songs in year range:")
        song_titles = []
        for song in songs:
            song_titles.append(song.title)
        print(song_titles)

        # Get data analysis - percentages by year
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.one_artist_several_keywords(songs, years, keywords)
        print("Percentages:")
        print(data_list)

        # Make example sentence
        example_string = f'Example: In {years[0]} , {str(data_list[0].get("n containing " + keywords[0]))} of the {data_list[0].get("n total")} songs by {artist} contained the word {keywords[0]}. That is {data_list[0].get("% containing " + keywords[0])} %.'

        # Make and name CSV file
        csv_file = self.make_csv(data_list)
        keywords_string = ' '.join([elem for elem in keywords])
        csv_file.name = f'Lyrics analysis {artist} {str(years[0])} - {str(years[-1])} {keywords_string}.csv'

        return csv_file, example_string

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
