class Data_analyzer:

    def __init__(self):
        self.test = "test"

    def analyze_data_oa(self, artist, keywords, year_range):
        """Returns data list of percentages by years for one artist, several keywords"""

        # Add keyword frequencies to artist_songs_list
        for keyword in keywords:
            self.add_keyword_to_artist_songs_list(artist.songs_list, keyword)

        # Create data_list
        data_list = []

        # Analyze each year in year range
        for year in year_range:
            songs_list_year = [song for song in artist.songs_list if song.year == year]
            data_list.append(self.make_data_row_oa(songs_list_year, keywords, year))

        # Analyze whole year range
        songs_list_whole_year_range = [song for song in artist.songs_list if song.year in year_range]
        title = str(year_range[0]) + "-" + str(year_range[-1]) + " total"
        data_list.append(self.make_data_row_oa(songs_list_whole_year_range, keywords, title))

        # Analyze songs with year outside of year range
        songs_list_outside_year_range = [song for song in artist.songs_list if song.year != "unknown year" and song.year not in year_range]
        data_list.append(self.make_data_row_oa(songs_list_outside_year_range, keywords, "other known year"))

        # Analyze songs with unknown year
        songs_list_unknown_year = [song for song in artist.songs_list if song.year == "unknown year"]
        data_list.append(self.make_data_row_oa(songs_list_unknown_year, keywords, "unknown year"))

        # Analyze all songs (total)
        total_object = self.make_data_row_oa(artist.songs_list, keywords, "total")
        data_list.append(total_object)

        return data_list

    def analyze_data_ok(self, keyword, artists, year_range):
        """Returns data list of percentages by years for one keyword, several artists"""

        # Add keyword frequencies to artist_songs_list
        for artist in artists:
            self.add_keyword_to_artist_songs_list(artist.songs_list, keyword)

        # Create all_songs_list and artists_names for use in row making
        all_songs_list = []
        for artist in artists:
            for song in artist.songs_list:
                all_songs_list.append(song)
        artists_names = [artist.name for artist in artists]

        # Create data_list
        data_list = []

        # Analyze each year in year range
        for year in year_range:
            songs_list_year = [song for song in all_songs_list if song.year == year]
            data_list.append(self.make_data_row_ok(songs_list_year, artists_names, keyword, year))

        # Analyze whole year range
        songs_list_whole_year_range = [song for song in all_songs_list if song.year in year_range]
        title = str(year_range[0]) + "-" + str(year_range[-1]) + " total"
        data_list.append(self.make_data_row_ok(songs_list_whole_year_range, artists_names, keyword, title))

        # Analyze songs with year outside of year range
        songs_list_outside_year_range = [song for song in all_songs_list if song.year != "unknown year" and song.year not in year_range]
        data_list.append(self.make_data_row_ok(songs_list_outside_year_range, artists_names, keyword, "other known year"))

        # Analyze songs with unknown year
        songs_list_unknown_year = [song for song in all_songs_list if song.year == "unknown year"]
        data_list.append(self.make_data_row_ok(songs_list_unknown_year, artists_names, keyword, "unknown year"))

        # Analyze all songs (total)
        total_object = self.make_data_row_ok(all_songs_list, artists_names, keyword, "total")
        data_list.append(total_object)

        return data_list

    def add_keyword_to_artist_songs_list(self, artist_songs_list, keyword):

        for song in artist_songs_list:

            if isinstance(keyword, str):
                if keyword not in song.keywords.keys():
                    song.keywords[keyword] = (song.lyrics.find(" " + keyword + " ") != -1)

            elif isinstance(keyword, list):
                for single_keyword in keyword:
                    if single_keyword not in song.keywords.keys():
                        song.keywords[single_keyword] = (song.lyrics.find(" " + single_keyword + " ") != -1)

    def make_data_row_oa(self, songs_list, keywords, title):

        row_object = {"Year": title}

        # Count number of total songs and add to dictionary
        num_of_songs = len(songs_list)
        row_object["songs total"] = num_of_songs

        for keyword in keywords:

            # Check number of songs with keyword
            num_of_songs_with_keyword = self.get_num_of_songs_with_keyword_in_songs_list(keyword, songs_list)

            # Write % and n
            if num_of_songs_with_keyword == 0:
                row_object["% with " + self.make_keyword_str(keyword)] = 0.0
            else:
                row_object["% with " + self.make_keyword_str(keyword)] = round(
                    num_of_songs_with_keyword / num_of_songs * 100, 1)
            row_object["songs with " + self.make_keyword_str(keyword)] = num_of_songs_with_keyword

        return row_object

    def make_data_row_ok(self, songs_list, artists_names, keyword, title):

        row_object = {"Year": title}

        # Count number of total songs and add to dictionary
        num_of_songs = len(songs_list)
        row_object["songs total"] = num_of_songs

        for artist in artists_names:

            songs_list_artist = [song for song in songs_list if song.artist == artist]

            # Count number of total songs and add to dictionary
            num_of_songs = len(songs_list_artist)
            row_object[artist + ":\nsongs total"] = num_of_songs

            # Check number of songs with keyword
            num_of_songs_with_keyword = self.get_num_of_songs_with_keyword_in_songs_list(keyword, songs_list_artist)

            # Write % and n
            if num_of_songs_with_keyword == 0:
                row_object[artist + ":\n% with " + self.make_keyword_str(keyword)] = 0.0
            else:
                row_object[artist + ":\n% with " + self.make_keyword_str(keyword)] = round(
                    num_of_songs_with_keyword / num_of_songs * 100, 1)
            row_object[artist + ":\nsongs with " + self.make_keyword_str(keyword)] = num_of_songs_with_keyword

        return row_object

    def make_keyword_str(self, keyword):
        # !! same method in analysis_creator !!

        if isinstance(keyword, str):
            keyword_str = '"' + keyword + '"'
        elif isinstance(keyword, list):
            keyword_str = '"' + '" or "'.join(keyword) + '"'

        return keyword_str

    def get_num_of_songs_with_keyword_in_songs_list(self, keyword, songs_list):
        num_of_songs_with_keyword = 0

        if isinstance(keyword, str):
            for song in songs_list:
                if song.keywords[keyword]:
                    num_of_songs_with_keyword += 1

        elif isinstance(keyword, list):
            for song in songs_list:
                if any(song.keywords[single_keyword] for single_keyword in keyword):
                    num_of_songs_with_keyword += 1

        return num_of_songs_with_keyword

