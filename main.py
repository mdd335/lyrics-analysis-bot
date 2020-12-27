from tabulate import tabulate
from dataanalysis import Data_analyzer
from geniusscrape import Genius_scraper


# User input
artist = "The Ji (Rapper)"
keyword = "du"
# year_list = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
year_list = [2016, 2017, 2018, 2019, 2020]


# Get songs from Genius
my_genius_scraper = Genius_scraper()
song_list = my_genius_scraper.get_song_list(artist, year_list)
print()
print("Found year and lyrics of " + str(len(song_list)) + " songs in year range:")
print(song_list)


# Get data analysis - percentages by year
my_data_analyzer = Data_analyzer()
years_percentages_list = my_data_analyzer.percentage_of_songs_with_keyword_per_year(song_list, year_list, keyword)
print("Percentages:")
print(years_percentages_list)
print()


# Print results
data_for_table = []
for year in years_percentages_list:
    data_for_table.append([year.get("Year"), year.get("Percentage"), year.get("n with keyword"), year.get("n total")])
output = tabulate(data_for_table, headers = ["Year", "%", "n with keyword", "n total"])

print("Artist: " + artist)
print("Keyword: " + keyword)
print()
print(output)
print()
print("Example: In " + str(years_percentages_list[0].get("Year")) + ", " + str(years_percentages_list[0].get("n with keyword")) + " of the " + str(years_percentages_list[0].get("n total")) + " songs by " + artist + " contain the word " + keyword + ". That is " + str(years_percentages_list[0].get("Percentage")) + " %.")