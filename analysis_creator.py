from data_analyzer import Data_analyzer
from genius_scraper import Genius_scraper

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import csv
import io


class Analysis_creator:

    def __init__(self):
        self.test = "test"

    def create_analysis(self, request):

        print(f'CREATING ANALYSIS: {request.method}, artists(s): {[artist.name for artist in request.artists]}, keyword(s): {request.keywords}')
        print()

        for artist in request.artists:
            # Check whether song list has to be scraped
            if artist.songs_list is None:
                # Get songs from Genius
                my_genius_scraper = Genius_scraper()
                artist.songs_list = my_genius_scraper.get_artist_songs_list(artist.id, artist.name)
                print()
                print(f'Scraped lyrics of {len(artist.songs_list)} songs by {artist.name}')
                print()
            else:
                # Take songs from artist_dictionary
                print()
                print(f'Song list of {len(artist.songs_list)} songs by {artist.name} taken from artist_dictionary')
                print()

        # Get data analysis list
        my_data_analyzer = Data_analyzer()
        data_list = my_data_analyzer.make_data_list(request)
        print("Percentages (data_list):")
        print(data_list)
        print()

        # Make info string
        info_string = ""
        info_string += self.make_years_without_lyrics_str(data_list)
        info_string += self.make_example_str(data_list, request)
        print("Created info string")

        # Make IMG file
        if request.method == "one_artist":
            img_file = self.make_img(request.artists[0].name, request.keywords, data_list, "one_artist", request.minimum_n_per_year)
        elif request.method == "one_keyword":
            img_file = self.make_img(request.keywords[0], [artist.name for artist in request.artists], data_list, "one_keyword", request.minimum_n_per_year)
        print("Created IMG file")

        # Make CSV file
        csv_file = self.make_csv(data_list)
        csv_file.name = self.make_csv_name_string(request)
        print("Created CSV file")

        return img_file, csv_file, info_string

    def make_years_without_lyrics_str(self, data_list):
        years_without_lyrics_str = [str(data_row["Year"]) for data_row in data_list if isinstance(data_row["Year"], int) and data_row["songs total"] == 0]
        if len(years_without_lyrics_str) > 0:
            return f"No lyrics found for {', '.join(years_without_lyrics_str)}.\n"
        else:
            return ""

    def make_example_str(self, data_list, request):
        if request.method == "one_artist":
            for data_row in data_list:
                if data_row["songs total"] != 0:
                    return f'Example: In {data_row["Year"]}, {data_row["songs with " + self.make_keyword_str(request.keywords[0])]} of the {data_row["songs total"]} {request.artists[0].name} songs that I found contained the term {self.make_keyword_str(request.keywords[0])}. That is {round(data_row["% with " + self.make_keyword_str(request.keywords[0])])} %.'
        elif request.method == "one_keyword":
            for data_row in data_list:
                if data_row["songs total"] != 0:
                    info_songs_with_keyword = data_row[request.artists[0].name + ":\nsongs with " + self.make_keyword_str(request.keywords[0])]
                    info_songs_total = data_row[request.artists[0].name + ":\nsongs total"]
                    info_percent_with_keyword = data_row[request.artists[0].name + ":\n% with " + self.make_keyword_str(request.keywords[0])]
                    return f'Example: In {data_row["Year"]}, {info_songs_with_keyword} of the {info_songs_total} {request.artists[0].name} songs that I found contained the term {self.make_keyword_str(request.keywords[0])}. That is {round(info_percent_with_keyword)} %.'

    def make_img(self, artist_or_keyword, keywords_or_artists, data_list, method, minimum_n_per_year):

        data_list_only_years = [data_row for data_row in data_list if isinstance(data_row["Year"], int)]

        # Create plot
        fig, ax = plt.subplots()

        # Grid
        plt.grid(b=None, which='major', axis='both', color="whitesmoke")

        for keyword_or_artist in keywords_or_artists:

            # Plots
            x, y = self.make_x_and_y_lists_for_plot(artist_or_keyword, data_list_only_years, keyword_or_artist, method, minimum_n_per_year)
            if method == "one_artist":
                ax.plot(x, y, label=self.make_keyword_str(keyword_or_artist), marker=".")
            elif method == "one_keyword":
                ax.plot(x, y, label=keyword_or_artist, marker=".")

            # Data point annotations
            if len(data_list_only_years) > 25:
                data_point_annotations_font_size = 4
            else:
                data_point_annotations_font_size = 6
            for i, txt in enumerate(y):
                ax.annotate(str(round(txt)) + "%", (x[i], y[i]), xytext=(10, 10), textcoords='offset pixels', color='dimgray', fontsize=data_point_annotations_font_size)

        # Title
        plt.title(self.make_img_title_str(artist_or_keyword, keywords_or_artists, method), pad=15, fontsize=9)

        # Bottom text
        ax.text(0.5, -0.115, 'source: lyrics on Genius.com - made with t.me/lyricsbot', verticalalignment='bottom', horizontalalignment='center', transform=ax.transAxes, color='dimgray', fontsize=6)

        # X-axis labels should not be decimal numbers (2010.5)
        ax.xaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10], integer=True))

        '''
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
        '''

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

    def make_x_and_y_lists_for_plot(self, artist_or_keyword, data_list_only_years, keyword_or_artist, method, minimum_n_per_year):
        x = []
        y = []
        for data_row in data_list_only_years:
            if method == "one_artist":
                if data_row["songs total"] >= minimum_n_per_year:
                    x.append(data_row["Year"])
                    y.append(data_row["% with " + self.make_keyword_str(keyword_or_artist)])
            elif method == "one_keyword":
                if data_row[keyword_or_artist + ":\nsongs total"] >= minimum_n_per_year:
                    x.append(data_row["Year"])
                    y.append(data_row[keyword_or_artist + ":\n% with " + self.make_keyword_str(artist_or_keyword)])
        return x, y

    def make_img_title_str(self, artist_or_keyword, keywords_or_artists, method):
        if method == "one_artist":
            if len(keywords_or_artists) > 1:
                return f'% of {artist_or_keyword} songs with different keywords in their lyrics, per year'
            else:
                return f'% of {artist_or_keyword} songs with {self.make_keyword_str(keywords_or_artists[0])} in their lyrics, per year'
        elif method == "one_keyword":
            if len(keywords_or_artists) > 1:
                return f'% of songs by different artists with {self.make_keyword_str(artist_or_keyword)} in their lyrics, per year'
            else:
                return f'% of {keywords_or_artists[0]} songs with {self.make_keyword_str(artist_or_keyword)} in their lyrics, per year'

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

    def make_csv_name_string(self, request):

        if request.method == "one_artist":
            keywords_string = ' '.join([self.make_keyword_str_no_quotations(elem) for elem in request.keywords])
            return f'Lyrics analysis {request.artists[0].name} {str(request.year_start)}-{str(request.year_end)} {keywords_string}.csv'
        elif request.method == "one_keyword":
            artists_string = ' '.join([artist.name for artist in request.artists])
            return f'Lyrics analysis {artists_string} {str(request.year_start)}-{str(request.year_start)} {self.make_keyword_str_no_quotations(request.keywords[0])}.csv'

    def make_keyword_str(self, keyword):
        # !! same method in data_analyzer !!

        if isinstance(keyword, str):
            keyword_str = '"' + keyword + '"'
        elif isinstance(keyword, list):
            keyword_str = '"' + '" or "'.join(keyword) + '"'

        return keyword_str

    def make_keyword_str_no_quotations(self, keyword):

        if isinstance(keyword, str):
            keyword_str = keyword
        elif isinstance(keyword, list):
            keyword_str = '-'.join(keyword)

        return keyword_str


