import os
import dotenv

dotenv.load_dotenv()

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
CHANNELS_FILE = os.path.join(REPO_ROOT, "channels.yml")
KEYWORDS_FILE = os.path.join(REPO_ROOT, "keywords.yml")
FEED_FILE = os.path.join(REPO_ROOT, "feed.xml")

SITE_TITLE = os.environ.get("FEED_TITLE", "Telegram Tech Channels Feed")
SITE_LINK  = os.environ.get("FEED_LINK",  "https://github.com")
SITE_DESC  = os.environ.get("FEED_DESC",  "Aggregated posts from Telegram channels for the last 7 days")
FEED_LIMIT = int(os.environ.get("FEED_LIMIT", "200"))  # total items in feed
FEED_DAYS = int(os.environ.get("FEED_DAYS", "7"))  # only include posts from last N days

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]