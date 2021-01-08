from analysis_creator import Analysis_creator
from user_request import User_request

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


ARTIST, KEYWORD, YEAR_START, YEAR_END, ANALYSIS = range(5)

request_dictionary = {}
artist_dictionary = {}

# TODO: Add method: one keyword, several artists


def start(update: Update, context: CallbackContext) -> int:
    clean_dictionaries()
    request_dictionary[update.message.chat.id] = User_request(update.message.chat.id)
    update.message.reply_text("Hey, I am the LyricsBot. If you tell me an artist, a time span and one or more keyword(s), I will tell you the percentage of their songs in each year in the time span that contain the keyword(s).")
    update.message.reply_text("Type /info for more detailed info. Type /start at any time to start from the beginning.")
    update.message.reply_text("First, please tell me the artist. Spell the name exactly as it is spelled on genius.com")
    # TODO: several artists as one (AKAs)

    return ARTIST


def info(update: Update, context: CallbackContext) -> int:
    # TODO: Add info
    update.message.reply_text("Info")
    update.message.reply_text("Info")
    update.message.reply_text("Info")
    update.message.reply_text(f'Type /start anytime to start.')

    return ConversationHandler.END


def artist_chosen(update: Update, context: CallbackContext) -> int:
    artist = update.message.text
    # TODO: check if right artist
    request_dictionary[update.message.chat.id].artist = artist
    if artist == "Money Boy":
        update.message.reply_text(f'Gute Wahl Mois')
    update.message.reply_text(f'I will analyze {artist}.')
    update.message.reply_text(f'Please choose the year in which the time span should start, e.g. 2010.')

    return YEAR_START


def yearstart_chosen(update: Update, context: CallbackContext) -> int:
    year_start = update.message.text
    if year_start.isnumeric():
        if len(year_start) == 4 and 1799 < int(year_start) < 2031:
            request_dictionary[update.message.chat.id].year_start = year_start
            update.message.reply_text(f'I will start with year {year_start}.')
            update.message.reply_text(f'Next, please choose the year in which the time span should end.')
            return YEAR_END
    update.message.reply_text(f'Please enter a start year between 1900 and 2030.')
    return YEAR_START


def yearend_chosen(update: Update, context: CallbackContext) -> int:
    year_end = update.message.text
    if year_end.isnumeric():
        if len(year_end) == 4 and int(request_dictionary[update.message.chat.id].year_start) <= int(year_end) < 2031:
            request_dictionary[update.message.chat.id].year_end = year_end
            update.message.reply_text(f'I will analyze the years between {request_dictionary[update.message.chat.id].year_start} and {year_end}.')
            update.message.reply_text(f'Next, please choose the first keyword to analyze.')
            # TODO: several keywords as one (synonyms)
            return KEYWORD
    update.message.reply_text(f'Please enter an end year between {request_dictionary[update.message.chat.id].year_start} (start year) and 2030.')
    return YEAR_END


def keyword_chosen(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text
    request_dictionary[update.message.chat.id].keywords.append(keyword)
    update.message.reply_text(f'You selected artist {request_dictionary[update.message.chat.id].artist}, time span {request_dictionary[update.message.chat.id].year_start} to {request_dictionary[update.message.chat.id].year_end} and keyword(s) {str(request_dictionary[update.message.chat.id].keywords)}.')
    update.message.reply_text(f'Add another keyword or type /analyze to start Analysis')

    return ANALYSIS


@run_async
def analysis_started(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Analysis started. This might take a while.')

    # Prepare and send request at Analysis Creator
    artist = request_dictionary[update.message.chat.id].artist
    if artist in artist_dictionary.keys():
        artist_songs_list = artist_dictionary[artist]
    else:
        artist_songs_list = None
    keywords = request_dictionary[update.message.chat.id].keywords
    year_range = list(range(int(request_dictionary[update.message.chat.id].year_start), int(request_dictionary[update.message.chat.id].year_end) + 1))
    my_analysis_creator = Analysis_creator()
    img_file, csv_file, example_string, artist_songs_list_new = my_analysis_creator.analyze_artist(artist, artist_songs_list, keywords, year_range)

    # Store artist song list in artist dictionary
    if artist not in artist_dictionary.keys():
        artist_dictionary[artist] = artist_songs_list_new

    # Send output to user
    context.bot.send_photo(chat_id=update.message.chat_id, photo=img_file)
    update.message.reply_text(f'Here is the data as a csv file (can be opened in Excel or similar apps):')
    context.bot.send_document(chat_id=update.message.chat_id, document=csv_file)
    update.message.reply_text(example_string)
    update.message.reply_text(f'Type /info for more detailed info on how the data was created. Type /start anytime to start over.')
    print("Analysis finished, output sent")
    print()

    # Remove request from request dictionary
    del request_dictionary[update.message.chat.id]

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



