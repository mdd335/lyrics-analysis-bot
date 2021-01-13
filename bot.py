from analysis_creator import Analysis_creator
from user_request import User_request
from genius_scraper import Genius_scraper
from artist import Artist

import logging
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from telegram.ext.dispatcher import run_async
import os


PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


METHOD, ARTIST_OA, ARTIST_CONF_OA, YEAR_START_OA, YEAR_END_OA, KEYWORD_OA, ANALYSIS_OA, KEYWORD_OK, YEAR_START_OK, YEAR_END_OK, ARTIST_OK, ARTIST_CONF_OK, ANALYSIS_OK = range(13)

request_dictionary = {}
artist_list = []


def start(update: Update, context: CallbackContext) -> int:
    clean_dictionaries()
    request_dictionary[update.message.chat.id] = User_request(update.message.chat.id)
    # TODO: add example pictures to start message
    update.message.reply_text("Hey, I am the LyricsBot 🤠\nIf you tell me an artist, a time span and one or more keywords, I will analyze the artists lyrics on Genius.com and tell you about their usage of the keyword(s), like in the image above. Send /info for more detailed info. Send /start at any time to start from the beginning.")
    update.message.reply_text("To start, please choose a method: send /oneartist to analyze one artist (compare up to 5 keywords) or /onekeyword to analyze one keyword (compare up to 5 artists).")

    return METHOD


def choose_artist_oa(update: Update, context: CallbackContext) -> int:
    # TODO: several artists as one (AKAs)
    request_dictionary[update.message.chat.id].method = "one_artist"
    update.message.reply_text("First, please tell me the artist you want to analyze.")
    return ARTIST_OA


def confirm_artist_oa(update: Update, context: CallbackContext) -> int:
    artist_search_str = update.message.text
    my_genius_scraper = Genius_scraper()
    artist_name, artist_url, artist_id = my_genius_scraper.get_artist_name_url_id(artist_search_str)

    request_dictionary[update.message.chat.id].artist_draft = Artist(artist_name, artist_id)

    artist_url = artist_url[artist_url.find('genius'):]
    update.message.reply_text(f'I have found {artist_name} ({artist_url}). If this is the right artist, send /continue. If not, please enter the name again. Try spelling it exactly as it is spelled on Genius.', disable_web_page_preview=True)

    return ARTIST_CONF_OA


def choose_year_start_oa(update: Update, context: CallbackContext) -> int:
    if request_dictionary[update.message.chat.id].artist_name == "Money Boy":
        update.message.reply_text(f'Gute Wahl Mois')

    request_dictionary[update.message.chat.id].artist = request_dictionary[update.message.chat.id].artist_draft

    update.message.reply_text(f'Please choose the year in which the time span should start, e.g. 2010.')

    return YEAR_START_OA


def choose_year_end_oa(update: Update, context: CallbackContext) -> int:
    year_start = update.message.text

    # Check if answer is numeric and between 1900 and 2030, otherwise ask again
    if not year_start.isnumeric() or (1899 >= int(year_start) or int(year_start) >= 2031):
        update.message.reply_text(f'Please enter a start year between 1900 and 2030.')
        return YEAR_START_OA

    # Answer
    request_dictionary[update.message.chat.id].year_start = year_start
    update.message.reply_text(f'Next, please choose the year in which the time span should end, e.g. 2020.')
    return YEAR_END_OA


def choose_first_keyword_oa(update: Update, context: CallbackContext) -> int:
    year_end = update.message.text

    # Check if answer is numeric and between start year and 2030, otherwise ask again
    if not year_end.isnumeric() or (int(request_dictionary[update.message.chat.id].year_start) > int(year_end) or int(year_end) >= 2031):
        update.message.reply_text(f'Please enter an end year between {request_dictionary[update.message.chat.id].year_start} (start year) and 2030.')
        return YEAR_END_OA

    # Answer
    request_dictionary[update.message.chat.id].year_end = year_end
    update.message.reply_text(f'I will analyze the years from {request_dictionary[update.message.chat.id].year_start} to {year_end}.\nNext, please choose the first keyword to analyze (no case sensitivity).')
    # TODO: several keywords as one (synonyms)
    return KEYWORD_OA


def add_keywords_oa(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text.lower()
    if len(request_dictionary[update.message.chat.id].keywords) < 5:
        request_dictionary[update.message.chat.id].keywords.append(keyword)

    keywords_string = ', '.join(['"' + elem + '"' for elem in request_dictionary[update.message.chat.id].keywords])
    if len(request_dictionary[update.message.chat.id].keywords) < 5:
        update.message.reply_text(f'Keyword(s): {keywords_string}.\nAdd another keyword or send /analyze to start Analysis.')
    else:
        update.message.reply_text(f'Keyword(s): {keywords_string}.\nMaximum of 5 keywords reached. Send /analyze to start Analysis.')

    return ANALYSIS_OA


def choose_keyword_ok(update: Update, context: CallbackContext) -> int:
    # TODO: several artists as one (AKAs)
    request_dictionary[update.message.chat.id].method = "one_keyword"
    update.message.reply_text("First, please tell me the keyword you want to analyze.")
    return KEYWORD_OK


def choose_year_start_ok(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text.lower()
    request_dictionary[update.message.chat.id].keyword = keyword
    update.message.reply_text(f'I will analyze "{keyword}".\nPlease choose the year in which the time span should start, e.g. 2010.')

    return YEAR_START_OK


def choose_year_end_ok(update: Update, context: CallbackContext) -> int:
    year_start = update.message.text

    # Check if answer is numeric and between 1900 and 2030, otherwise ask again
    if not year_start.isnumeric() or (1899 >= int(year_start) or int(year_start) >= 2031):
        update.message.reply_text(f'Please enter a start year between 1900 and 2030.')
        return YEAR_START_OK

    # Answer
    request_dictionary[update.message.chat.id].year_start = year_start
    update.message.reply_text(f'Next, please choose the year in which the time span should end, e.g. 2020.')
    return YEAR_END_OK


def choose_first_artist_ok(update: Update, context: CallbackContext) -> int:
    year_end = update.message.text

    # Check if answer is numeric and between start year and 2030, otherwise ask again
    if not year_end.isnumeric() or (int(request_dictionary[update.message.chat.id].year_start) > int(year_end) or int(year_end) >= 2031):
        update.message.reply_text(f'Please enter an end year between {request_dictionary[update.message.chat.id].year_start} (start year) and 2030.')
        return YEAR_END_OK

    # Answer
    request_dictionary[update.message.chat.id].year_end = year_end
    update.message.reply_text(f'I will analyze the years from {request_dictionary[update.message.chat.id].year_start} to {year_end}.\nNext, please choose the first artist to analyze.')
    return ARTIST_OK


def confirm_artist_ok(update: Update, context: CallbackContext) -> int:
    artist_search_str = update.message.text
    my_genius_scraper = Genius_scraper()
    artist_name, artist_url, artist_id = my_genius_scraper.get_artist_name_url_id(artist_search_str)

    request_dictionary[update.message.chat.id].artist_draft = Artist(artist_name, artist_id)

    artist_url = artist_url[artist_url.find('genius'):]
    update.message.reply_text(f'I have found {artist_name} ({artist_url}). If this is the right artist, send /continue. If not, please enter the name again. Try spelling it exactly as it is spelled on Genius.', disable_web_page_preview=True)

    return ARTIST_CONF_OK


def add_artists_ok(update: Update, context: CallbackContext) -> int:
    if len(request_dictionary[update.message.chat.id].artists) < 5:
        if request_dictionary[update.message.chat.id].artist_draft.name == "Money Boy":
            update.message.reply_text(f'Gute Wahl Mois')
        request_dictionary[update.message.chat.id].artists.append(request_dictionary[update.message.chat.id].artist_draft)

    artists_string = ', '.join([artist.name for artist in request_dictionary[update.message.chat.id].artists])
    if len(request_dictionary[update.message.chat.id].artists) < 5:
        update.message.reply_text(f'Artist(s): {artists_string}.\nAdd another artist or send /analyze to start Analysis.')
    else:
        update.message.reply_text(f'Artist(s): {artists_string}.\nMaximum of 5 artists reached. Send /analyze to start Analysis.')

    return ANALYSIS_OK


@run_async
def get_analysis(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Analysis started. This might take a while. (If I havent answered after 10 minutes, there was probably an error. Please try again later or try other artist/keywords.)')

    year_range = list(range(int(request_dictionary[update.message.chat.id].year_start), int(request_dictionary[update.message.chat.id].year_end) + 1))

    if request_dictionary[update.message.chat.id].method == "one_artist":

        # Prepare request
        artist_new = request_dictionary[update.message.chat.id].artist
        keywords = request_dictionary[update.message.chat.id].keywords
        artist_from_list = next((artist for artist in artist_list if artist.name == artist_new.name), None)
        if artist_from_list is not None:
            artist_new.songs_list = artist_from_list.songs_list

        # Send request and store new artist in artist_list
        my_analysis_creator = Analysis_creator()
        img_file, csv_file, info_string, artist_new = my_analysis_creator.create_analysis_oa(artist_new, keywords, year_range)
        if artist_from_list is None:
            artist_list.append(artist_new)

    elif request_dictionary[update.message.chat.id].method == "one_keyword":

        # Prepare request
        keyword = request_dictionary[update.message.chat.id].keyword
        artists = request_dictionary[update.message.chat.id].artists
        for artist_new in artists:
            artist_from_list = next((artist for artist in artist_list if artist.name == artist_new.name), None)
            if artist_from_list is not None:
                artist_new.songs_list = artist_from_list.songs_list

        # Send request and store new artists in artist_list
        my_analysis_creator = Analysis_creator()
        img_file, csv_file, info_string, artists_new = my_analysis_creator.create_analysis_ok(keyword, request_dictionary[update.message.chat.id].artists, year_range)
        for artist_new in artists_new:
            artist_from_list = next((artist for artist in artist_list if artist.name == artist_new.name), None)
            if artist_from_list is None:
                artist_list.append(artist_new)

    # Send output to user
    context.bot.send_photo(chat_id=update.message.chat_id, photo=img_file)
    update.message.reply_text(info_string)
    update.message.reply_text(f'Here is the more detailed data as a csv file (can be opened in Excel or similar apps):')
    context.bot.send_document(chat_id=update.message.chat_id, document=csv_file)
    update.message.reply_text(f'Send /info for more detailed info on how the data was created. Send /start anytime to start over.')
    print("Analysis finished, output sent")
    print()

    # Remove request from request dictionary
    del request_dictionary[update.message.chat.id]

    return ConversationHandler.END


def info(update: Update, context: CallbackContext) -> int:
    # TODO: Add info
    update.message.reply_text("*How does it work?* Info", parse_mode="Markdown")
    update.message.reply_text("Info")
    update.message.reply_text("Info")
    update.message.reply_text(f'Send /start anytime to start.')

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("***REMOVED_TELEGRAM_BOT_TOKEN***", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states ...
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('info', info)
        ],
        states={
            METHOD: [
                CommandHandler('start', start),
                CommandHandler('info', info),
                CommandHandler('oneartist', choose_artist_oa),
                CommandHandler('onekeyword', choose_keyword_ok)
            ],
            ARTIST_OA: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, confirm_artist_oa)
            ],
            ARTIST_CONF_OA: [
                CommandHandler('start', start),
                CommandHandler('continue', choose_year_start_oa),
                MessageHandler(Filters.text, confirm_artist_oa)
            ],
            YEAR_START_OA: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_year_end_oa)
            ],
            YEAR_END_OA: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_first_keyword_oa)
            ],
            KEYWORD_OA: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, add_keywords_oa)
            ],
            ANALYSIS_OA: [
                CommandHandler('start', start),
                CommandHandler('analyze', get_analysis),
                MessageHandler(Filters.text, add_keywords_oa)
            ],
            KEYWORD_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_year_start_ok)
            ],
            YEAR_START_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_year_end_ok)
            ],
            YEAR_END_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_first_artist_ok)
            ],
            ARTIST_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, confirm_artist_ok)
            ],
            ARTIST_CONF_OK: [
                CommandHandler('start', start),
                CommandHandler('continue', add_artists_ok),
                MessageHandler(Filters.text, confirm_artist_ok)
            ],
            ANALYSIS_OK: [
                CommandHandler('start', start),
                CommandHandler('analyze', get_analysis),
                MessageHandler(Filters.text, confirm_artist_ok)
            ]
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot with Heroku backend
    # updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path="***REMOVED_TELEGRAM_BOT_TOKEN***")
    # updater.bot.setWebhook('https://murmuring-stream-73575.herokuapp.com/' + "***REMOVED_TELEGRAM_BOT_TOKEN***")

    # Start the Bot with local backend
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def clean_dictionaries():
    if len(artist_list) > 1000:
        artist_list.clear()

    if len(request_dictionary) > 1000:
        request_dictionary.clear()


if __name__ == '__main__':
    main()

