class Data_analyzer:

    def __init__(self):
        self.test = "test"

    def one_artist_several_keywords(self, artist_songs_list, year_range, keywords):
        """Returns data list of percentages by years for one artist, several keywords"""

        self.add_keywords_to_artist_songs_list(artist_songs_list, keywords)

        data_list = []

        # Analyze each year in year range
        for year in year_range:
            songs_list_year = [song for song in artist_songs_list if song.year == year]
            data_list.append(self.make_data_row_oa(songs_list_year, keywords, year))

        # Analyze whole year range
        songs_list_whole_year_range = [song for song in artist_songs_list if song.year in year_range]
        title = str(year_range[0]) + "-" + str(year_range[-1]) + " total"
        data_list.append(self.make_data_row_oa(songs_list_whole_year_range, keywords, title))

        # Analyze songs with year outside of year range
        songs_list_outside_year_range = [song for song in artist_songs_list if song.year != "unknown year" and song.year not in year_range]
        data_list.append(self.make_data_row_oa(songs_list_outside_year_range, keywords, "other known year"))

        # Analyze songs with unknown year
        songs_list_unknown_year = [song for song in artist_songs_list if song.year == "unknown year"]
        data_list.append(self.make_data_row_oa(songs_list_unknown_year, keywords, "unknown year"))

        # Analyze all songs (total)
        total_object = self.make_data_row_oa(artist_songs_list, keywords, "total")
        data_list.append(total_object)

        return data_list

    def add_keywords_to_artist_songs_list(self, artist_songs_list, keywords):
        for song in artist_songs_list:
            for keyword in keywords:

                if not hasattr(song, 'keywords'):
                    song.keywords = {}

                if keyword not in song.keywords.keys():
                    song.keywords[keyword] = (song.lyrics.find(keyword) != -1)

    def make_data_row_oa(self, songs_list, keywords, title):

        row_object = {"Year": title}

        # Count number of total songs and add to dictionary
        num_of_songs = len(songs_list)
        row_object["n total"] = num_of_songs

        for keyword in keywords:

            # Check number of songs with keyword for each keyword
            num_of_songs_with_keyword = 0
            for song in songs_list:
                if song.keywords[keyword]:
                    num_of_songs_with_keyword += 1

            # Write % and n for each keyword
            if num_of_songs_with_keyword == 0:
                row_object["% containing " + keyword] = 0.0
            else:
                row_object["% containing " + keyword] = round(num_of_songs_with_keyword / num_of_songs * 100, 1)
            row_object["n containing " + keyword] = num_of_songs_with_keyword

        return row_object

