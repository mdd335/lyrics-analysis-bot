from data_analyzer import Data_analyzer
from genius_scraper import Genius_scraper
from artist import Artist

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import csv
import io


class Analysis_creator:

    def __init__(self):
        self.test = "test"

    def create_analysis_oa(self, artist, keywords, year_range):

        # Check whether song list has to be scraped
        if artist.songs_list is None:
            # Get songs from Genius
            my_genius_scraper = Genius_scraper()
            artist.songs_list = my_genius_scraper.get_artist_songs_list(artist.id, artist.name)
            print()
            print(f'Found lyrics of {len(artist.songs_list)} songs by {artist.name}:')
        else:
            # Take songs from artist_dictionary
            print()
            print(f'Song list of {len(artist.songs_list)} songs by {artist.name} taken from artist_dictionary:')

        # Make list of song titles
        song_titles = [song.title for song in artist.songs_list]
        print(song_titles)

        # Get data analysis - percentages by year
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.analyze_data_oa(artist, keywords, year_range)
        print("Percentages (data_list):")
        print(data_list)

        # Make info string
        info_string = ""
        info_string += self.make_years_without_lyrics_str(data_list)
        for data_row in data_list:
            if data_row["songs total"] != 0:
                info_string += f'Example: In {data_row["Year"]}, {data_row["songs with " + keywords[0]]} of the {data_row["songs total"]} songs by {artist.name} contained the term "{keywords[0]}". That is {round(data_row["% with " + keywords[0]])} %.'
                break

        # Make IMG file
        img_file = self.make_img(artist.name, keywords, data_list, "one_artist")

        # Make and name CSV file
        csv_file = self.make_csv(data_list)
        keywords_string = ' '.join([elem for elem in keywords])
        csv_file.name = f'Lyrics analysis {artist.name} {str(year_range[0])}-{str(year_range[-1])} {keywords_string}.csv'

        return img_file, csv_file, info_string, artist

    def create_analysis_ok(self, keyword, artists, year_range):

        for artist in artists:
            # Check whether song list has to be scraped
            if artist.songs_list is None:
                # Get songs from Genius
                my_genius_scraper = Genius_scraper()
                artist.songs_list = my_genius_scraper.get_artist_songs_list(artist.id, artist.name)
                print()
                print(f'Found lyrics of {len(artist.songs_list)} songs by {artist.name}:')
            else:
                # Take songs from artist_dictionary
                print()
                print(f'Song list of {len(artist.songs_list)} songs by {artist.name} taken from artist_dictionary:')

            # Make list of song titles
            song_titles = [song.title for song in artist.songs_list]
            print(song_titles)
            print()

        # Get data analysis - percentages by year
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.analyze_data_ok(keyword, artists, year_range)
        print("Percentages (data_list):")
        print(data_list)

        # Make info string
        info_string = ""
        info_string += self.make_years_without_lyrics_str(data_list)
        for data_row in data_list:
            if data_row["songs total"] != 0:
                info_songs_with_keyword = data_row[artists[0].name + ":\nsongs with " + keyword]
                info_songs_total = data_row[artists[0].name + ":\nsongs total"]
                info_percent_with_keyword = data_row[artists[0].name + ":\n% with " + keyword]
                info_string += f'Example: In {data_row["Year"]}, {info_songs_with_keyword} of the {info_songs_total} songs by {artists[0].name} contained the term "{keyword}". That is {round(info_percent_with_keyword)} %.'
                break


        # Make IMG file
        img_file = self.make_img(keyword, [artist.name for artist in artists], data_list, "one_keyword")

        # Make and name CSV file
        csv_file = self.make_csv(data_list)
        artists_string = ' '.join([artist.name for artist in artists])
        csv_file.name = f'Lyrics analysis {artists_string} {str(year_range[0])}-{str(year_range[-1])} {keyword}.csv'

        return img_file, csv_file, info_string, artists

    def make_years_without_lyrics_str(self, data_list):
        years_without_lyrics_str = [str(data_row["Year"]) for data_row in data_list if isinstance(data_row["Year"], int) and data_row["songs total"] == 0]
        if len(years_without_lyrics_str) > 0:
            return f"No lyrics found for {', '.join(years_without_lyrics_str)}.\n"
        else:
            return ""

    def make_img_ALT(self, artist_name, keywords, data_list):

        data_list_only_years = [data_row for data_row in data_list if isinstance(data_row["Year"], int)]

        # Create plot
        fig, ax = plt.subplots()

        # Grid
        plt.grid(b=None, which='major', axis='y')

        # Graph lines
        for keyword in keywords:

            x = []
            y = []
            for data_row in data_list_only_years:
                if data_row["songs total"] != 0:
                    x.append(data_row["Year"])
                    y.append(data_row["% with " + keyword])

            ax.plot(x, y, label=keyword, marker=".")

            # Data point annotations
            if len(data_list_only_years) < 25:
                for i, txt in enumerate(y):
                    ax.annotate(str(round(txt)) + "%", (x[i], y[i]), xytext=(10, 10), textcoords='offset pixels', color='dimgray', fontsize=6)

        # Title
        if len(keywords) > 1:
            plt.title(f'% of {artist_name} songs with different keywords in their lyrics, per year', pad=15)
        else:
            plt.title(f'% of {artist_name} songs with "{keywords[0]}" in their lyrics, per year', pad=15)

        # Bottom text
        ax.text(0.5, -0.135, 'source: lyrics on Genius.com - made with t.me/lyricsbot',
                verticalalignment='bottom', horizontalalignment='center',
                transform=ax.transAxes,
                color='dimgray', fontsize=6)

        # X-axis labels should not be decimal numbers (2010.5)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        # X-axis label annotations (n =)
        try:
            if len(data_list_only_years) < 10:
                x_years = [data_row["Year"] for data_row in data_list_only_years]
                x_n = [data_row["songs total"] for data_row in data_list_only_years]
                x_locs, x_labels = plt.xticks()
                xticks_new = [str(year) + "\nn=" + str(x_n[i]) for i, year in enumerate(x_years)]
                plt.xticks(x_locs[1:-1], xticks_new)
        except:
            print("Error while trying to add n= to X-axis labels")

        # Y-axis label annotations (%)
        try:
            y_locs, y_labels = plt.yticks()
            yticks_new = [str(int(loc)) + "%" for loc in list(y_locs)[1:-1]]
            plt.yticks(y_locs[1:-1], yticks_new)
        except:
            print("Error while trying to add % to Y-axis labels")

        # Legend
        if len(keywords) > 1:
            ax.legend()

        # Make file
        img_file = io.BytesIO()
        img_file.name = 'image.jpeg'
        plt.savefig(img_file, format='JPEG', dpi=200)
        img_file.seek(0)

        return img_file

    def make_img(self, artist_or_keyword, keywords_or_artists, data_list, method):

        data_list_only_years = [data_row for data_row in data_list if isinstance(data_row["Year"], int)]

        # Create plot
        fig, ax = plt.subplots()

        # Grid
        plt.grid(b=None, which='major', axis='y')

        # Graph lines
        for keyword_or_artist in keywords_or_artists:

            x = []
            y = []
            for data_row in data_list_only_years:
                if method == "one_artist":
                    if data_row["songs total"] != 0:
                        x.append(data_row["Year"])
                        y.append(data_row["% with " + keyword_or_artist])
                elif method == "one_keyword":
                    if data_row[keyword_or_artist + ":\nsongs total"] != 0:
                        x.append(data_row["Year"])
                        y.append(data_row[keyword_or_artist + ":\n% with " + artist_or_keyword])

            ax.plot(x, y, label=keyword_or_artist, marker=".")

            # Data point annotations
            if len(data_list_only_years) < 25:
                for i, txt in enumerate(y):
                    ax.annotate(str(round(txt)) + "%", (x[i], y[i]), xytext=(10, 10), textcoords='offset pixels', color='dimgray', fontsize=6)

        # Title
        if method == "one_artist":
            if len(keywords_or_artists) > 1:
                plt.title(f'% of {artist_or_keyword} songs with different keywords in their lyrics, per year', pad=15)
            else:
                plt.title(f'% of {artist_or_keyword} songs with "{keywords_or_artists[0]}" in their lyrics, per year', pad=15)
        elif method == "one_keyword":
            if len(keywords_or_artists) > 1:
                plt.title(f'% of songs by different artists with "{artist_or_keyword}" in their lyrics, per year', pad=15)
            else:
                plt.title(f'% of {keywords_or_artists[0]} songs with "{artist_or_keyword}" in their lyrics, per year', pad=15)

        # Bottom text
        ax.text(0.5, -0.135, 'source: lyrics on Genius.com - made with t.me/lyricsbot',
                verticalalignment='bottom', horizontalalignment='center',
                transform=ax.transAxes,
                color='dimgray', fontsize=6)

        # X-axis labels should not be decimal numbers (2010.5)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        # X-axis label annotations (n =)
        if method == "one_artist":
            try:
                if len(data_list_only_years) < 10:
                    x_years = [data_row["Year"] for data_row in data_list_only_years]
                    x_n = [data_row["songs total"] for data_row in data_list_only_years]
                    x_locs, x_labels = plt.xticks()
                    xticks_new = [str(year) + "\nn=" + str(x_n[i]) for i, year in enumerate(x_years)]
                    plt.xticks(x_locs[1:-1], xticks_new)
            except:
                print("Error while trying to add n= to X-axis labels")

        # Y-axis label annotations (%)
        try:
            y_locs, y_labels = plt.yticks()
            yticks_new = [str(int(loc)) + "%" for loc in list(y_locs)[1:-1]]
            plt.yticks(y_locs[1:-1], yticks_new)
        except:
            print("Error while trying to add % to Y-axis labels")

        # Legend
        if len(keywords_or_artists) > 1:
            ax.legend()

        # Make file
        img_file = io.BytesIO()
        img_file.name = 'image.jpeg'
        plt.savefig(img_file, format='JPEG', dpi=250)
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
