from analysis_creator import Analysis_creator
from user_request import User_request
from genius_scraper import Genius_scraper

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


ARTIST, ARTIST_CONFIRMATION, KEYWORD, YEAR_START, YEAR_END, ANALYSIS = range(6)

request_dictionary = {}
artist_dictionary = {}

# TODO: Add method: one keyword, several artists


def start(update: Update, context: CallbackContext) -> int:
    clean_dictionaries()
    request_dictionary[update.message.chat.id] = User_request(update.message.chat.id)
    # TODO: add example pictures to start message
    update.message.reply_text("Hey, I am the LyricsBot 🤠\nIf you tell me an artist, a time span and one or more keywords, I will analyze the artists lyrics on Genius.com and tell you about their usage of the keyword(s), like in the image above. Type /info for more detailed info. Type /start at any time to start from the beginning.")
    update.message.reply_text("First, please tell me the artist you want to analyze.")
    # TODO: several artists as one (AKAs)

    return ARTIST


def artist_chosen(update: Update, context: CallbackContext) -> int:
    artist_search_str = update.message.text
    my_genius_scraper = Genius_scraper()
    artist_name, artist_url, artist_id = my_genius_scraper.get_artist_name_url_id(artist_search_str)

    request_dictionary[update.message.chat.id].artist_name = artist_name
    request_dictionary[update.message.chat.id].artist_id = artist_id

    artist_url = artist_url[artist_url.find('genius'):]
    update.message.reply_text(f'I have found {artist_name} ({artist_url}). If this is the right artist, type /continue. If not, please enter the name again. Try spelling it exactly as it is spelled on Genius.com.', disable_web_page_preview=True)

    return ARTIST_CONFIRMATION


def artist_confirmed(update: Update, context: CallbackContext) -> int:
    if request_dictionary[update.message.chat.id].artist_name == "Money Boy":
        update.message.reply_text(f'Gute Wahl Mois')
    update.message.reply_text(f'Please choose the year in which the time span should start, e.g. 2010.')

    return YEAR_START


def yearstart_chosen(update: Update, context: CallbackContext) -> int:
    year_start = update.message.text

    # Check if answer is numeric and between 1900 and 2030, otherwise ask again
    if not year_start.isnumeric() or (1899 >= int(year_start) or int(year_start) >= 2031):
        update.message.reply_text(f'Please enter a start year between 1900 and 2030.')
        return YEAR_START

    # Answer
    request_dictionary[update.message.chat.id].year_start = year_start
    update.message.reply_text(f'Next, please choose the year in which the time span should end, e.g. 2020.')
    return YEAR_END


def yearend_chosen(update: Update, context: CallbackContext) -> int:
    year_end = update.message.text

    # Check if answer is numeric and between start year and 2030, otherwise ask again
    if not year_end.isnumeric() or (int(request_dictionary[update.message.chat.id].year_start) > int(year_end) or int(year_end) >= 2031):
        update.message.reply_text(f'Please enter an end year between {request_dictionary[update.message.chat.id].year_start} (start year) and 2030.')
        return YEAR_END

    # Answer
    request_dictionary[update.message.chat.id].year_end = year_end
    update.message.reply_text(f'I will analyze the years from {request_dictionary[update.message.chat.id].year_start} to {year_end}.\nNext, please choose the first keyword to analyze (no case sensitivity).')
    # TODO: several keywords as one (synonyms)
    return KEYWORD


def keyword_chosen(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text.lower()
    request_dictionary[update.message.chat.id].keywords.append(keyword)
    keywords_string = ', '.join(['"' + elem + '"' for elem in request_dictionary[update.message.chat.id].keywords])
    # update.message.reply_text(f'You selected artist {request_dictionary[update.message.chat.id].artist_name}, time span {request_dictionary[update.message.chat.id].year_start} to {request_dictionary[update.message.chat.id].year_end} and keyword(s) {str(request_dictionary[update.message.chat.id].keywords)}.')
    update.message.reply_text(f'Keyword(s): {keywords_string}.\nAdd another keyword or type /analyze to start Analysis.')

    return ANALYSIS


@run_async
def analysis_started(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Analysis started. This might take a while. (If I havent answered after 10 minutes, there was probably an error. Please try again later or try other artist/keywords.)')

    # Prepare and send request at Analysis Creator
    artist_name = request_dictionary[update.message.chat.id].artist_name
    artist_id = request_dictionary[update.message.chat.id].artist_id
    if artist_name in artist_dictionary.keys():
        artist_songs_list = artist_dictionary[artist_name]
    else:
        artist_songs_list = None
    keywords = request_dictionary[update.message.chat.id].keywords
    year_range = list(range(int(request_dictionary[update.message.chat.id].year_start), int(request_dictionary[update.message.chat.id].year_end) + 1))
    my_analysis_creator = Analysis_creator()
    img_file, csv_file, info_string, artist_songs_list_new = my_analysis_creator.analyze_artist(artist_name, artist_id, artist_songs_list, keywords, year_range)

    # Check for "Error" return
    if isinstance(img_file, str):
        update.message.reply_text(f'Could not load songs by artist 😳\nPlease try again later or try another artist. Type /start to start.')
        del request_dictionary[update.message.chat.id]
        return ConversationHandler.END

    # Store artist_songs_list in artist_dictionary
    if artist_name not in artist_dictionary.keys():
        artist_dictionary[artist_name] = artist_songs_list_new

    # Send output to user
    context.bot.send_photo(chat_id=update.message.chat_id, photo=img_file)
    update.message.reply_text(info_string)
    update.message.reply_text(f'Here is the more detailed data as a csv file (can be opened in Excel or similar apps):')
    context.bot.send_document(chat_id=update.message.chat_id, document=csv_file)
    update.message.reply_text(f'Type /info for more detailed info on how the data was created. Type /start anytime to start over.')
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
    update.message.reply_text(f'Type /start anytime to start.')

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
            ARTIST: [
                CommandHandler('start', start),
                CommandHandler('info', info),
                MessageHandler(Filters.text, artist_chosen)
            ],
            ARTIST_CONFIRMATION: [
                CommandHandler('start', start),
                CommandHandler('continue', artist_confirmed),
                MessageHandler(Filters.text, artist_chosen)
            ],
            YEAR_START: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, yearstart_chosen)
            ],
            YEAR_END: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, yearend_chosen)
            ],
            KEYWORD: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, keyword_chosen)
            ],
            ANALYSIS: [
                CommandHandler('start', start),
                CommandHandler('analyze', analysis_started),
                MessageHandler(Filters.text, keyword_chosen)
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
    if len(artist_dictionary) > 1000:
        artist_dictionary.clear()

    if len(request_dictionary) > 1000:
        request_dictionary.clear()


if __name__ == '__main__':
    main()



