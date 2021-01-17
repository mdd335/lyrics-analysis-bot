class User_request:

    def __init__(self, chat_id):

        self.chat_id = chat_id

        self.method = None

        self.artist_drafts = None

        self.artists = []

        self.year_start = None

        self.year_end = None

        self.keywords = []

        self.minimum_n_per_year = 1

