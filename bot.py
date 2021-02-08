from analysis_creator import Analysis_creator
from user_request import User_request
from genius_scraper import Genius_scraper
from artist import Artist

import logging
import datetime
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from telegram.ext.dispatcher import run_async
import os


PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

current_year = datetime.datetime.now().year

METHOD, ARTIST_OA, ARTIST_CONF_OA, KEYWORD_OA, ANALYSIS_OA, KEYWORD_OK, ARTIST_OK, ARTIST_CONF_OK, ANALYSIS_OK = range(9)

request_dictionary = {}
artist_list = []

# TODO: several artists as one (AKAs)


def start(update: Update, context: CallbackContext) -> int:
    clean_dictionaries()
    request_dictionary[update.message.chat.id] = User_request(update.message.chat.id)
    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text("Hey, I am the LyricsBot 🤠\nIf you tell me artist(s) and keyword(s), I will analyze the artists lyrics on [Genius](www.genius.com) and create statistics about how often they contain the keyword(s). Send /info for more detailed info. Send /example for examples. Send /start anytime to restart.", parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
    update.message.reply_text("To start, please choose a method: send /artist to analyze 1 artist (compare usage of up to 10 keywords) or /keyword to analyze 1 keyword (compare lyrics of up to 4 artists).")
    return METHOD


def choose_artist_oa(update: Update, context: CallbackContext) -> int:
    request_dictionary[update.message.chat.id].method = "one_artist"
    update.message.reply_text("First, please tell me the artist you want to analyze.")
    return ARTIST_OA


def confirm_artist_oa(update: Update, context: CallbackContext) -> int:
    artist_search_str = update.message.text
    artist_suggestions = get_artist_search_results(artist_search_str)
    if len(artist_suggestions) == 0:
        update.message.reply_text(f'No artist found. Please check spelling and enter the artist again.')
        return ARTIST_OA
    request_dictionary[update.message.chat.id].artist_drafts = artist_suggestions
    reply_markup = make_artist_reply_keyboard(artist_suggestions)
    artists_string = ', '.join([f'[{artist_suggestion["name"]}]({artist_suggestion["url"]})' for artist_suggestion in artist_suggestions])
    update.message.reply_text(f'I found (Genius pages are linked): {artists_string}. Please choose the right artist.', parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)

    return ARTIST_CONF_OA


def choose_first_keyword_oa(update: Update, context: CallbackContext) -> int:

    # Check artist confirmation
    artist_confirmation_str = update.message.text
    reply_markup = ReplyKeyboardRemove()
    if artist_confirmation_str == "Money Boy":
        update.message.reply_text(f'Gute Wahl Mois', reply_markup=reply_markup)
    if "None of those" in artist_confirmation_str:
        update.message.reply_text(f'Try spelling the artist exactly as it is spelled on [Genius](www.genius.com). If I still dont suggest the right artist, try entering a unique album or song title of the artist instead. Please enter the artist again.', parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
        return ARTIST_OA
    elif not any(artist_confirmation_str == artist_draft['name'] for artist_draft in request_dictionary[update.message.chat.id].artist_drafts):
        update.message.reply_text(f'Something didnt work. Please enter the artist again. Make sure to use the Telegram keyboard buttons to confirm the artist in the next step.', reply_markup=reply_markup)
        return ARTIST_OA
    else:
        add_artist_from_drafts_matching_string_to_artists(artist_confirmation_str, request_dictionary[update.message.chat.id])

    # Ask for first keyword
    update.message.reply_text(f'Next, please choose the first keyword to analyze (no case sensitivity).')
    return KEYWORD_OA


def add_keywords_oa(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text.lower()

    # Check for minimum=X input
    if keyword.startswith("minimum="):
        set_minimum_n_per_year(keyword, update, "keyword")
        return ANALYSIS_OA

    # Check for years=X input
    if keyword.startswith("years="):
        set_year_span(keyword, update, "keyword")
        return ANALYSIS_OA

    # Check spelling and type (OR?) of input. If correct, add to request.keywords
    if any(elem in keyword for elem in [".", ",", ":", ";", "(", ")", "!", "?", "\'", "\"", "#"]):
        update.message.reply_text(f'Punctuation and special characters dont work in keywords. Please only use letters and numbers. Use blank spaces if you are interested in word combinations, e.g. "i am". Use "/" to check if songs contain one OR the other keyword, e.g. "america/usa". Please enter the keyword again.')
        return KEYWORD_OA
    elif len(request_dictionary[update.message.chat.id].keywords) < 10:
        if "/" in keyword:
            request_dictionary[update.message.chat.id].keywords.append(keyword.split("/"))
        else:
            request_dictionary[update.message.chat.id].keywords.append(keyword)

    # Answer
    num_of_keywords = len(request_dictionary[update.message.chat.id].keywords)
    keywords_string = make_keywords_string(request_dictionary[update.message.chat.id])
    if num_of_keywords == 1:
        update.message.reply_text(f'{num_of_keywords} Keyword: {keywords_string}.\nAdd another keyword or send /analyze to start analysis.')
    elif num_of_keywords == 4:
        update.message.reply_text(f'{num_of_keywords} Keywords: {keywords_string}.\nFor a good looking graph, I suggest using no more than 4-5 keywords. Add another keyword or send /analyze to start analysis.')
    elif num_of_keywords < 10:
        update.message.reply_text(f'{num_of_keywords} Keywords: {keywords_string}.\nAdd another keyword or send /analyze to start analysis.')
    else:
        update.message.reply_text(f'{num_of_keywords} Keywords: {keywords_string}.\nMaximum of 10 keywords reached. Send /analyze to start analysis.')
    return ANALYSIS_OA


def choose_keyword_ok(update: Update, context: CallbackContext) -> int:
    request_dictionary[update.message.chat.id].method = "one_keyword"
    update.message.reply_text("First, please tell me the keyword you want to analyze (no case sensitivity).")
    return KEYWORD_OK


def choose_first_artist_ok(update: Update, context: CallbackContext) -> int:

    # Check spelling and type (OR?) of input. If correct, add to request.keywords and create keyword_str
    keyword = update.message.text.lower()
    if any(elem in keyword for elem in [".", ",", ":", ";", "(", ")", "!", "?", "\'", "\"", "#"]):
        update.message.reply_text(f'Punctuation and special characters dont work in keywords. Please only use letters and numbers. Use blank spaces if you are interested in word combinations, e.g. "i am". Use "/" to check if songs contain one OR the other keyword, e.g. "america/usa". Please enter the keyword again.')
        return KEYWORD_OK
    elif "/" in keyword:
        request_dictionary[update.message.chat.id].keywords.append(keyword.split("/"))
        keyword_str = '("' + '" or "'.join(keyword.split("/")) + '")'
    else:
        request_dictionary[update.message.chat.id].keywords.append(keyword)
        keyword_str = '"' + keyword + '"'

    # Ask for first artist
    update.message.reply_text(f'I will analyze {keyword_str}. Next, please choose the first artist to analyze.')
    return ARTIST_OK


def confirm_artist_ok(update: Update, context: CallbackContext) -> int:
    artist_search_str = update.message.text

    # Check for minimum=X input
    if artist_search_str.lower().startswith("minimum="):
        set_minimum_n_per_year(artist_search_str, update, "artist")
        return ANALYSIS_OK

    # Check for years=X input
    if artist_search_str.lower().startswith("years="):
        set_year_span(artist_search_str, update, "artist")
        return ANALYSIS_OK

    # Otherwise, show artist suggestions
    artist_suggestions = get_artist_search_results(artist_search_str)
    if len(artist_suggestions) == 0:
        update.message.reply_text(f'No artist found. Please check spelling and enter the artist again.')
        return ARTIST_OK
    request_dictionary[update.message.chat.id].artist_drafts = artist_suggestions
    reply_markup = make_artist_reply_keyboard(artist_suggestions)
    artists_string = ', '.join([f'[{artist_suggestion["name"]}]({artist_suggestion["url"]})' for artist_suggestion in artist_suggestions])
    update.message.reply_text(f'I found (Genius pages are linked): {artists_string}. Please choose the right artist.', parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
    return ARTIST_CONF_OK


def add_artists_ok(update: Update, context: CallbackContext) -> int:
    artist_confirmation_str = update.message.text
    reply_markup = ReplyKeyboardRemove()

    # Check artist confirmation
    if len(request_dictionary[update.message.chat.id].artists) < 4:
        if artist_confirmation_str == "Money Boy":
            update.message.reply_text(f'Gute Wahl Mois', reply_markup=reply_markup)
        if "None of those" in artist_confirmation_str:
            update.message.reply_text(f'Try spelling the artist exactly as it is spelled on [Genius](www.genius.com). If I still dont suggest the right artist, try entering a unique album or song title of the artist instead. Please enter the artist again.', parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
            return ARTIST_OK
        elif not any(artist_confirmation_str == artist_draft['name'] for artist_draft in request_dictionary[update.message.chat.id].artist_drafts):
            update.message.reply_text(f'Something didnt work. Please enter the artist again. Make sure to use the Telegram keyboard buttons to confirm the artist in the next step.', reply_markup=reply_markup)
            return ARTIST_OK
        else:
            add_artist_from_drafts_matching_string_to_artists(artist_confirmation_str, request_dictionary[update.message.chat.id])

    # Ask for next artist
    num_of_artists = len(request_dictionary[update.message.chat.id].artists)
    artists_string = ', '.join([artist.name for artist in request_dictionary[update.message.chat.id].artists])
    if num_of_artists == 1:
        update.message.reply_text(f'{num_of_artists} Artist: {artists_string}.\nAdd another artist or send /analyze to start analysis.', reply_markup=reply_markup)
    elif num_of_artists < 4:
        update.message.reply_text(f'{num_of_artists} Artists: {artists_string}.\nAdd another artist or send /analyze to start analysis.', reply_markup=reply_markup)
    else:
        update.message.reply_text(f'{num_of_artists} Artists: {artists_string}.\nMaximum of 4 artists reached. Send /analyze to start analysis.', reply_markup=reply_markup)
    return ANALYSIS_OK


@run_async
def get_analysis(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Analysis started. This might take a while. (If I havent answered after 20min, there was probably an error. Please try again later or try other artists/keywords. Send /start to restart.)')

    # Add songs list(s) to artist(s) if they are already in artist_list
    artists = request_dictionary[update.message.chat.id].artists
    for artist_new in artists:
        artist_from_list = next((artist for artist in artist_list if artist.name == artist_new.name), None)
        if artist_from_list is not None:
            artist_new.songs_list = artist_from_list.songs_list

    # Send request
    my_analysis_creator = Analysis_creator()
    img_file, csv_file, info_string = my_analysis_creator.create_analysis(request_dictionary[update.message.chat.id])

    # Store new artists in artist_list
    for artist_new in artists:
        artist_from_list = next((artist for artist in artist_list if artist.name == artist_new.name), None)
        if artist_from_list is None:
            artist_list.append(artist_new)

    # Send output to user
    context.bot.send_photo(chat_id=update.message.chat_id, photo=img_file)
    update.message.reply_text(info_string)
    update.message.reply_text(f'Here is the more detailed data as a csv file (can be opened in Excel or similar apps):')
    context.bot.send_document(chat_id=update.message.chat_id, document=csv_file)
    update.message.reply_text(f'Send /info for more detailed info on how the data was created. Send /start anytime to restart.')
    print("Analysis finished, output sent")
    print()

    # Remove request from request dictionary
    del request_dictionary[update.message.chat.id]

    return ConversationHandler.END


def info_start(update: Update, context: CallbackContext) -> int:
    send_info(update)
    update.message.reply_text("Send /example for examples. To start, please choose a method: send /artist to analyze 1 artist (compare usage of up to 10 keywords) or /keyword to analyze 1 keyword (compare lyrics of up to 4 artists).")

    return METHOD


def info_end(update: Update, context: CallbackContext) -> int:
    send_info(update)
    update.message.reply_text(f'Send /start anytime to restart.')

    return ConversationHandler.END


def example(update: Update, context: CallbackContext) -> int:
    photo_list = [InputMediaPhoto(open('examples/kanye.jpg', 'rb')), InputMediaPhoto(open('examples/love.jpg', 'rb')), InputMediaPhoto(open('examples/gucci_mane.jpg', 'rb')), InputMediaPhoto(open('examples/bitch.jpg', 'rb'))]
    context.bot.send_media_group(chat_id=update.message.chat.id, media=photo_list)

    update.message.reply_text("Send /info for more detailed info about the bot. To start, please choose a method: send /artist to analyze 1 artist (compare usage of up to 10 keywords) or /keyword to analyze 1 keyword (compare lyrics of up to 4 artists).")

    return METHOD


def main() -> None:
    # Create the Updater and pass it your bots token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("***REMOVED_TELEGRAM_BOT_TOKEN***", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states ...
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('info', info_end)
        ],
        states={
            METHOD: [
                CommandHandler('start', start),
                CommandHandler('info', info_start),
                CommandHandler('example', example),
                CommandHandler('artist', choose_artist_oa),
                CommandHandler('keyword', choose_keyword_ok)
            ],
            ARTIST_OA: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, confirm_artist_oa)
            ],
            ARTIST_CONF_OA: [
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
                MessageHandler(Filters.text, choose_first_artist_ok)
            ],
            ARTIST_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, confirm_artist_ok)
            ],
            ARTIST_CONF_OK: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, add_artists_ok)
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
    # TODO: do not delete newest artists/requests when cleaning
    if len(artist_list) > 1000:
        artist_list.clear()

    if len(request_dictionary) > 1000:
        request_dictionary.clear()


def make_artist_reply_keyboard(artist_suggestions):
    custom_keyboard = []
    custom_keyboard_row_draft = []
    for i, suggestion in enumerate(artist_suggestions):
        custom_keyboard_row_draft.append(suggestion["name"])
        if i % 2 == 1:
            custom_keyboard.append(custom_keyboard_row_draft)
            custom_keyboard_row_draft = []
    if len(artist_suggestions) % 2 == 1:
        custom_keyboard.append([artist_suggestions[-1]["name"], "❌ None of those"])
    else:
        custom_keyboard.append(["❌ None of those"])
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True, one_time_keyboard=True)
    return reply_markup


def get_artist_search_results(artist_search_str):
    my_genius_scraper = Genius_scraper()
    artist_suggestions = my_genius_scraper.get_artist_name_url_id_of_first_4(artist_search_str)
    if len(artist_suggestions) > 9:
        artist_suggestions = artist_suggestions[:9]
    return artist_suggestions


def make_keywords_string(request):
    list_for_keywords_string = []
    for keyword in request.keywords:
        if isinstance(keyword, str):
            list_for_keywords_string.append('"' + keyword + '"')
        elif isinstance(keyword, list):
            list_for_keywords_string.append(' or '.join(['"' + elem + '"' for elem in keyword]))
    keywords_string = ', '.join(list_for_keywords_string)
    return keywords_string


def add_artist_from_drafts_matching_string_to_artists(artist_confirmation_str, request):
    for artist_draft in request.artist_drafts:
        if artist_draft["name"] == artist_confirmation_str:
            request.artists.append(Artist(artist_draft["name"], artist_draft["id"]))


def set_minimum_n_per_year(input, update, keyword_or_artist):
    minimum_n_per_year = input.lower()[input.lower().find('minimum=') + 8:]
    if minimum_n_per_year.isnumeric():
        minimum_n_per_year = int(minimum_n_per_year)
        if minimum_n_per_year == 0:
            minimum_n_per_year = 1
        if minimum_n_per_year > 0:
            request_dictionary[update.message.chat.id].minimum_n_per_year = minimum_n_per_year
            update.message.reply_text(f'Graph will have data points for years with at least {minimum_n_per_year} total songs. Add another {keyword_or_artist} or send /analyze to start analysis.')
            return

    update.message.reply_text(f'Please enter a number (1 or higher) as minimum. Try again or add another {keyword_or_artist} or send /analyze to start analysis.')


def set_year_span(input, update, keyword_or_artist):
    start_index = input.lower().find('years=')
    year_start_input = input.lower()[start_index + 6: start_index + 10]
    year_end_input = input.lower()[start_index + 11: start_index + 15]

    try:
        if year_start_input.isnumeric() and 1900 <= int(year_start_input) < current_year:
            if year_end_input.isnumeric() and int(year_start_input) < int(year_end_input) <= current_year:
                request_dictionary[update.message.chat.id].custom_year_span = True
                request_dictionary[update.message.chat.id].year_start = int(year_start_input)
                request_dictionary[update.message.chat.id].year_end = int(year_end_input)
                update.message.reply_text(f'I will analyze the years from {year_start_input} to {year_end_input}. Add another {keyword_or_artist} or send /analyze to start analysis.')
                return
    except:
        print("Error with year span input")

    update.message.reply_text(f'Please enter a year span between 1900 and today, e.g. "years=2010-2020". Try again or add another {keyword_or_artist} or send /analyze to start analysis.')


def send_info(update):
    update.message.reply_text(
        '*How does it work?* For each artist in your request, I get a list of their songs as a main artist from the Genius API. For all these songs (if an artist has >900 songs, I take a random sample of 900), I check the lyrics page and try to get the release year (works 99 % of the time) and lyrics. I remove all punctuation, special characters and text in squared brackets from the lyrics. (I then store this data internally for ~12h to be faster if the same artist is requested again.) Then I search the lyrics of each song for the keyword(s) you gave me, sort by years and generate a graph (.jpg) and a table (.csv) based on that.\n'
        '*Entering artists:* I use your input as a search term on Genius and suggest the artists that come up. Please use the Telegram custom keyboard that I provide to choose the right artist or choose "None of those" if your artist is not one of the suggestions.\n'
        '*Keywords:* I check if exactly this term (without case sensitivity) appears in the lyrics as a whole word. So the keyword „hi“ matches the word "hi" or „Hi“ but not „hit“. Use blank spaces if you are interested in word combinations, e.g. "i am". Use "/" to check if songs contain one OR the other keyword, e.g. "america/usa". Punctuation in the lyrics is regarded as blank spaces, so to find „R.I.P.“ you would have to enter „r i p“.\n'
        '*minimum=:* By default, I only make data points in the graph for years in which the artist has a minimum of 5 total songs. You can change this by sending „minimum=X“ (with X being a number) when asked for keywords/artists in the last step. A higher number can make the graph look better because there are less outliers. Set to 1 to include all years.\n'
        '*years=:* By default, I include all years in the graph and table in which at least one of the artist(s) has at least 5 (or minimum=X) total songs. If you are only interested in a certain time span, you can change this by sending „years=XXXX-XXXX“ (with XXXX being years) when asked for keywords/artists in the last step.\n'
        '*Feature parts:* I cant distinguish between different artists on one song. So if a song has a feature part by another artist, those lyrics are considered, too.\n'
        '*If I dont respond:* If I am creating an analysis, please wait up to 20min for me to finish. Otherwise, send /start to restart. If I still dont respond, the bot is offline for some reason. Try again later/tomorrow.\n'
        '*Other bugs:* If there seems to be some other problem, please restart and try other artists/keywords/years. Also, feel free to write an email and describe the bug.\n'
        '*Contact:* If you have questions or feedback, please contact dripdroparchiv@gmail.com. Not affiliated with Genius, shoutout to them.',
        parse_mode="Markdown")


if __name__ == '__main__':
    main()
