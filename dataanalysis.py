from song import Song


def analyze_by_years(song_list, years_list, keyword):
    """Returns list of percentages by years"""

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
            percentage = num_of_songs_with_keyword / num_of_songs

        years_percentages_list.append({"Year": year, "Percentage": percentage, "n with keyword": num_of_songs_with_keyword, "n total": num_of_songs})

    return years_percentages_list
