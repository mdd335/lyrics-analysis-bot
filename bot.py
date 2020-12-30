from analysis_creator import Analysis_creator

import logging
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import os

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


artists = []
keywords = []
years = []

ARTIST, KEYWORD, YEAR_START, YEAR_END, ANALYSIS = range(5)


def start(update: Update, context: CallbackContext) -> int:
    artists.clear()
    keywords.clear()
    years.clear()
    update.message.reply_text("Hi! I am the LyricsBot.")
    update.message.reply_text("If you tell me an artist, a time span and one or more keyword(s), I will tell you the percentage of their songs in each year in the time span that contain the keyword(s).")
    update.message.reply_text("Type /info for more detailed info. Type /start at any time to start from the beginning.")
    update.message.reply_text("First, please tell me the artist. Spell the name exactly as it is spelled on genius.com")

    return ARTIST


def info(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Info")
    update.message.reply_text("Info")
    update.message.reply_text("Info")
    if artists == []:
        update.message.reply_text("Type in an artist to start. Spell the name exactly as it is spelled on genius.com")
        return ARTIST
    else:
        update.message.reply_text(f'Type /start anytime to start over.')
        return ConversationHandler.END


def artist_chosen(update: Update, context: CallbackContext) -> int:
    artist = update.message.text
    artists.append(artist)
    if artist == "Money Boy":
        update.message.reply_text(f'Gute Wahl Mois')
    update.message.reply_text(f'I will analyze {artist}.')
    update.message.reply_text(f'Please choose the year in which the time span should start, e.g. 2010.')

    return YEAR_START


def yearstart_chosen(update: Update, context: CallbackContext) -> int:
    yearstart = update.message.text
    if yearstart.isnumeric():
        if len(yearstart) == 4 and 1799 < int(yearstart) < 2031:
            years.append(int(yearstart))
            update.message.reply_text(f'I will start with year {yearstart}.')
            update.message.reply_text(f'Next, please choose the year in which the time span should end.')
            return YEAR_END
    update.message.reply_text(f'Please enter a year between 1900 and 2030.')
    return YEAR_START


def yearend_chosen(update: Update, context: CallbackContext) -> int:
    yearend = update.message.text
    if yearend.isnumeric():
        if len(yearend) == 4 and years[0] <= int(yearend) < 2031:
            years.append(int(yearend))
            update.message.reply_text(f'I will analyze the years between {str(years[0])} and {yearend}.')
            update.message.reply_text(f'Next, please choose the first keyword to analyze.')
            return KEYWORD
    update.message.reply_text(f'Please enter a year between {str(years[0])} and 2030.')
    return YEAR_END


def keyword_chosen(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text
    keywords.append(keyword)
    update.message.reply_text(f'You selected the artist "{artists[0]}", the time span {years[0]} to {years[1]} and keyword(s) {str(keywords)}.')
    update.message.reply_text(f'Add another keyword or type /analyze to start Analysis')

    return ANALYSIS


def analysis_started(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Analysis started. This might take a while.')
    my_analysis_creator = Analysis_creator()
    csv_file, example_string = my_analysis_creator.analyze_artist(artists[0], keywords, range(years[0], (years[1] + 1)))
    update.message.reply_text(f'Here is the data as a csv file:')
    context.bot.send_document(chat_id=update.message.chat_id, document=csv_file)
    update.message.reply_text(example_string)
    update.message.reply_text(f'Thank you. Type /start anytime to start over.')

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("***REMOVED_TELEGRAM_BOT_TOKEN***", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
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

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path="***REMOVED_TELEGRAM_BOT_TOKEN***")
    updater.bot.setWebhook('https://murmuring-stream-73575.herokuapp.com/' + "***REMOVED_TELEGRAM_BOT_TOKEN***")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()