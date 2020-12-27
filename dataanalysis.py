from song import Song


class Data_analyzer:

    def __init__(self):
        self.test = "test"

    def one_artist_several_keywords(self, songs, years, keywords):
        """Returns data list of percentages by years for one artist, several keywords"""

        data_list = []

        for year in years:

            # Count number of total songs in year
            num_of_songs = 0
            for song in songs:
                if song.year == year:
                    num_of_songs += 1

            # Get percentage and n for each keyword
            percentages_and_n_list = []
            for keyword in keywords:
                percentage, n_with_keyword = self.one_artist_one_keyword_one_year(songs, year, keyword)
                percentages_and_n_list.append({"Keyword": keyword, "%": percentage, "n": n_with_keyword})

            # Fill data list
            data_list.append({"Year": year, "n total": num_of_songs, "Keyword data": percentages_and_n_list})

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
            percentage = 0
        else:
            percentage = (n_with_keyword / num_of_songs) * 100

        return percentage, n_with_keyword





    def percentage_of_songs_with_keyword_per_year(self, song_list, years_list, keyword):
        """Returns list of percentages by years for one artist, one keyword"""

        keyword = " " + keyword + " "
        years_percentages_list = []

        for year in years_list:

            num_of_songs = 0
            num_of_songs_with_keyword = 0
            num_of_songs_without_keyword = 0

            for song in song_list:
                if song.year == year:
                    num_of_songs +=1
                    if song.lyrics.find(keyword) == -1:
                        num_of_songs_without_keyword += 1
                    else:
                        num_of_songs_with_keyword += 1

            if num_of_songs == 0:
                percentage = 0
            else:
                percentage = (num_of_songs_with_keyword / num_of_songs) * 100

            years_percentages_list.append({"Year": year, "Percentage": percentage, "n with keyword": num_of_songs_with_keyword, "n total": num_of_songs})

        return years_percentages_list
