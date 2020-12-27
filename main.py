import dataanalysis
from geniusscrape import Genius_scraper
from tabulate import tabulate


# User input
artist = "The Ji (Rapper)"
keyword = "ja"
years_list = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]


# Get songs from Genius
my_genius_scraper = Genius_scraper()
song_list = my_genius_scraper.get_song_list(artist)
print("")
print("Found year and lyrics of {} songs:".format(len(song_list)))
print(song_list)


# Get data analysis - percentages by year
years_percentages_list = dataanalysis.analyze_by_years(song_list, years_list, keyword)
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