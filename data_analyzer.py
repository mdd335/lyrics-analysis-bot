class Data_analyzer:

    def __init__(self):
        self.test = "test"


    def make_data_list(self, request):
        """Returns data list of percentages by years for one keyword, several artists"""

        # Add keyword frequencies to artist_songs_lists
        for artist in request.artists:
            for keyword in request.keywords:
                self.add_keyword_to_artist_songs_list(artist.songs_list, keyword)

        # Set year_start and year_end if not custom
        self.set_year_start_and_year_end_if_not_custom(request)

        # make year range
        year_range = list(range(request.year_start, request.year_end + 1))

        # Make artists_names
        artists_names = [artist.name for artist in request.artists]

        # Make all songs list
        if request.method == "one_artist":
            all_songs_list = request.artists[0].songs_list
        elif request.method == "one_keyword":
            all_songs_list = []
            for artist in request.artists:
                all_songs_list.extend(artist.songs_list)

        # Create data_list
        data_list = []

        # Analyze each year in year range
        for year in year_range:
            songs_list_year = [song for song in all_songs_list if song.year == year]
            row_object = self.make_data_row(songs_list_year, artists_names, request.keywords, year, request.method)
            if row_object["songs total"] > 0:
                data_list.append(row_object)

        if request.custom_year_span:
            # Analyze whole year range
            songs_list_whole_year_range = [song for song in all_songs_list if song.year in year_range]
            title = str(year_range[0]) + "-" + str(year_range[-1]) + " total"
            data_list.append(self.make_data_row(songs_list_whole_year_range, artists_names, request.keywords, title, request.method))

            # Analyze songs with year outside of year range
            songs_list_outside_year_range = [song for song in all_songs_list if song.year != "unknown year" and song.year not in year_range]
            data_list.append(self.make_data_row(songs_list_outside_year_range, artists_names, request.keywords, "other known year", request.method))

        # Analyze songs with unknown year
        songs_list_unknown_year = [song for song in all_songs_list if song.year == "unknown year"]
        data_list.append(self.make_data_row(songs_list_unknown_year, artists_names, request.keywords, "unknown year", request.method))

        # Analyze all songs (total)
        total_object = self.make_data_row(all_songs_list, artists_names, request.keywords, "total", request.method)
        data_list.append(total_object)

        return data_list

    def set_year_start_and_year_end_if_not_custom(self, request):
        if not request.custom_year_span:
            years = []
            for artist in request.artists:
                for song in artist.songs_list:
                    if isinstance(song.year, int) and song.year not in years:
                        years.append(song.year)
            request.year_start = min(years)
            request.year_end = max(years)

    def make_data_row(self, songs_list, artists_names, keywords, title, method):

        row_object = {"Year": title}

        # Count number of total songs and add to dictionary
        num_of_songs = len(songs_list)
        row_object["songs total"] = num_of_songs

        if method == "one_artist":

            for keyword in keywords:
                self.make_percent_and_n_cells(keyword, num_of_songs, row_object, songs_list)

        elif method == "one_keyword":

            for artist in artists_names:

                songs_list_artist = [song for song in songs_list if song.artist == artist]
                artist_str_for_cell_title = artist + ":\n"

                # Count number of total songs and add to dictionary
                num_of_songs = len(songs_list_artist)
                row_object[artist_str_for_cell_title + "songs total"] = num_of_songs

                self.make_percent_and_n_cells(keywords[0], num_of_songs, row_object, songs_list_artist, artist_str_for_cell_title)

        return row_object

    def make_percent_and_n_cells(self, keyword, num_of_songs, row_object, songs_list, artist_str_for_cell_title=""):

        # Check number of songs with keyword
        num_of_songs_with_keyword = self.get_num_of_songs_with_keyword_in_songs_list(keyword, songs_list)

        # Write % and n
        if num_of_songs_with_keyword == 0:
            row_object[artist_str_for_cell_title + "% with " + self.make_keyword_str(keyword)] = 0.0
        else:
            row_object[artist_str_for_cell_title + "% with " + self.make_keyword_str(keyword)] = round(num_of_songs_with_keyword / num_of_songs * 100, 1)
        row_object[artist_str_for_cell_title + "songs with " + self.make_keyword_str(keyword)] = num_of_songs_with_keyword

    def add_keyword_to_artist_songs_list(self, artist_songs_list, keyword):

        for song in artist_songs_list:

            if isinstance(keyword, str):
                if keyword not in song.keywords.keys():
                    song.keywords[keyword] = (song.lyrics.find(" " + keyword + " ") != -1)

            elif isinstance(keyword, list):
                for single_keyword in keyword:
                    if single_keyword not in song.keywords.keys():
                        song.keywords[single_keyword] = (song.lyrics.find(" " + single_keyword + " ") != -1)

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

