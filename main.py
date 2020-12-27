from dataanalysis import Data_analyzer
from geniusscrape import Genius_scraper
from tabulate import tabulate


# User input
artist = "Money Boy"
keywords = ["swag", "fly", "lit", "drip"]
years = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]


# Get songs from Genius
my_genius_scraper = Genius_scraper()
songs = my_genius_scraper.get_song_list(artist, years)
print()
print("Found year and lyrics of " + str(len(songs)) + " songs in year range:")
song_titles = []
for song in songs:
    song_titles.append(song.title)
print(song_titles)


# Get data analysis - percentages by year
my_data_analyzer = Data_analyzer()
data_list = my_data_analyzer.one_artist_several_keywords(songs, years, keywords)
print("Percentages:")
print(data_list)
print()


# Make table
data_for_table = []
for year in data_list:
    year_data = {"Year": year.get("Year"), "n total": year.get("n total")}
    for keyword in year.get("Keyword data"):
        keyword_string = keyword.get("Keyword")
        year_data["% containing " + keyword_string] = keyword.get("%")
        year_data["n containing " + keyword_string] = keyword.get("n")
    data_for_table.append(year_data)
output = tabulate(data_for_table, headers="keys")


# Print table
print("Artist: " + artist)
print("Keywords: " + str(keywords))
print()
print(output)
print()
print("Example: In " + str(data_list[0].get("Year")) + ", " + str(data_list[0].get("Keyword data")[0].get("n")) + " of the " + str(data_list[0].get("n total")) + " songs by " + artist + " contain the word " + keywords[0] + ". That is " + str(data_list[0].get("Keyword data")[0].get("%")) + " %.")