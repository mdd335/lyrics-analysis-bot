import geniusscrape
import dataanalysis
from tabulate import tabulate


artist = "Antilopen Gang"
keyword = "nmzs"
# time_span_start = 2010
# time_span_end = 2020
years_list = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]


# Get songs as main artist
songs = geniusscrape.get_song_id(geniusscrape.get_artist_id(artist))
songs_ids = [song["id"] for song in songs
    if song["primary_artist"]["id"] == artist_id]
print("Found {} songs as main artist:".format(len(songs_ids)))
print(songs_ids)
print("")

# Get song data, remove songs without year
songs_data_list = [geniusscrape.retrieve_lyrics(song_id) for song_id in songs_ids]
songs_data_list_cleaned = [song for song in songs_data_list if song != "no year found"]
print("Found year and lyrics of {} songs:".format(len(songs_data_list_cleaned)))
print(songs_data_list_cleaned)
print("")

# Get data analysis - percentages by year
years_percentages_list = dataanalysis.analyze_by_years(songs_data_list_cleaned, years_list, keyword)
print("Percentages:")
print(years_percentages_list)
print("")

# Print results
data_for_table = []

for year in years_percentages_list:
    data_for_table.append([year.get("Year"), year.get("Percentage"), year.get("n with keyword"), year.get("n total")])

output = tabulate(data_for_table, headers = ["Year", "%", "n with keyword", "n total"])

print("Artist: {}".format(artist))
print("Keyword: {}".format(keyword))
print("")
print(output)