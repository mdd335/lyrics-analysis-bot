from data_analyzer import Data_analyzer
from genius_scraper import Genius_scraper

import matplotlib.pyplot as plt
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
            print("Song list of " + str(len(artist_songs_list)) + " Songs taken from artist_dictionary:")

        # Make list of song titles
        song_titles = []
        for song in artist_songs_list:
            song_titles.append(song.title)
        print(song_titles)

        # Get data analysis - percentages by year
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.one_artist_several_keywords(artist_songs_list, year_range, keywords)
        print("Percentages:")
        print(data_list)

        # Make example sentence
        example_string = f'Example: In {year_range[0]}, {str(data_list[0].get("n containing " + keywords[0]))} of the {data_list[0].get("n total")} songs by {artist} contained the word {keywords[0]}. That is {data_list[0].get("% containing " + keywords[0])} %.'

        # Make IMG file
        img_file = self.make_img(artist, keywords, data_list)

        # Make and name CSV file
        csv_file = self.make_csv(data_list)
        keywords_string = ' '.join([elem for elem in keywords])
        csv_file.name = f'Lyrics analysis {artist} {str(year_range[0])} - {str(year_range[-1])} {keywords_string}.csv'

        return img_file, csv_file, example_string, artist_songs_list

    def make_img(self, artist, keywords, data_list):

        # Create plot
        fig, ax = plt.subplots()

        # Make lists for x- and y-axis data point positions
        for keyword in keywords:

            # x-axis
            x = []
            x_n =[]
            for year in data_list:
                yearstr = str(year["Year"])
                if yearstr != "other known year" and yearstr != "unknown year" and "total" not in yearstr:
                    x_n.append(year["n total"])
                    x.append(yearstr)

            # y-axis
            y = []
            for year in data_list:
                yearstr = str(year["Year"])
                if yearstr != "other known year" and yearstr != "unknown year" and "total" not in yearstr:
                    y.append(year["% containing " + keyword])

            ax.plot(x, y, label=keyword)

            # Make data point annotations
            for i, txt in enumerate(y):
                ax.annotate(str(round(txt)) + "%", (x[i], y[i]), xytext=(10, 0), textcoords='offset pixels', color='dimgray', fontsize=7)

        # Title
        plt.title(f'% of {artist} songs that contain different keywords, per year')

        # Text in corner
        ax.text(1, -0.13, 'source: lyrics on genius.com - made with t.me/lyricsbot',
                verticalalignment='bottom', horizontalalignment='right',
                transform=ax.transAxes,
                color='dimgray', fontsize=7)

        # X-axis annotations (n =)
        x_locs, x_labels = plt.xticks()
        xticks_new = [str(year) + "\nn=" + str(x_n[i]) for i, year in enumerate(x)]
        plt.xticks(x_locs, xticks_new)

        # Y-axis annotations (%)
        y_locs, y_labels = plt.yticks()
        yticks_new = [str(int(loc)) + "%" for loc in list(y_locs)[1:-1]]
        plt.yticks(y_locs[1:-1], yticks_new)

        # Legend
        ax.legend()

        # Make file
        img_file = io.BytesIO()
        img_file.name = 'image.jpeg'
        plt.savefig(img_file, format='JPEG')
        img_file.seek(0)

        return img_file

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

        return csv_file
