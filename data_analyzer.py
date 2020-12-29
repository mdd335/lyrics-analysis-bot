class Data_analyzer:

    def __init__(self):
        self.test = "test"

    def one_artist_several_keywords(self, songs, years, keywords):
        """Returns data list of percentages by years for one artist, several keywords"""

        data_list = []

        for year in years:

            # Create dictionary for year
            year_object = {"Year": year}

            # Count number of total songs in year and add to dictionary
            num_of_songs = 0
            for song in songs:
                if song.year == year:
                    num_of_songs += 1
            year_object["n total"] = num_of_songs

            # Get percentage and n for each keyword and add to dictionary
            for keyword in keywords:
                percentage, n_with_keyword = self.one_artist_one_keyword_one_year(songs, year, keyword)
                year_object["% containing " + keyword] = percentage
                year_object["n containing " + keyword] = n_with_keyword

            data_list.append(year_object)

        # Create last row (total)
        total_object = {"Year": "all years", "n total": len(songs)}
        for keyword in keywords:
            percentage, n_with_keyword = self.one_artist_one_keyword_all_years(songs, keyword)
            total_object["% containing " + keyword] = percentage
            total_object["n containing " + keyword] = n_with_keyword
        data_list.append(total_object)

        return data_list

    def one_artist_one_keyword_one_year(self, songs, year, keyword):
        """Returns list of percentages by years for one artist, one keyword, one year"""

        keyword = " " + keyword + " "

        num_of_songs = 0
        n_with_keyword = 0

        for song in songs:
            if song.year == year:
                num_of_songs += 1
                if song.lyrics.find(keyword) != -1:
                    n_with_keyword += 1

        if num_of_songs == 0:
            percentage = 0.0
        else:
            percentage = round(n_with_keyword / num_of_songs * 100, 1)

        return percentage, n_with_keyword

    def one_artist_one_keyword_all_years(self, songs, keyword):
        """Returns list of percentages for one artist, one keyword, all years"""

        keyword = " " + keyword + " "

        n_with_keyword = 0

        for song in songs:
            if song.lyrics.find(keyword) != -1:
                n_with_keyword += 1

        if len(songs) == 0:
            percentage = 0
        else:
            percentage = round(n_with_keyword / len(songs) * 100, 1)

        return percentage, n_with_keyword
