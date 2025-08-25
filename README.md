# Telegram to RSS Adapter

A GitHub Actions-powered adapter that converts Telegram channel posts into an RSS feed, hosted on GitHub Pages. Perfect for aggregating tech news from multiple Telegram channels into a single feed that can be consumed by RSS readers or AI tools like Perplexity Comet.

## Features

- 📱 Reads public Telegram channels using MTProto user client (no bot limitations)
- 🔍 Optional keyword filtering to reduce noise
- 🔄 Automatic updates every 15 minutes via GitHub Actions
- 📰 Standard RSS 2.0 format output
- 🌐 Free hosting on GitHub Pages
- 📊 Stateful tracking to avoid duplicate posts
- 🔗 Preserves links from original posts

## Quick Start

### 1. Prerequisites

- GitHub account
- Telegram account
- Python 3.11+ (for initial setup only)

### 2. Get Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Save your `api_id` and `api_hash`

### 3. Fork/Clone This Repository

```bash
git clone https://github.com/yourusername/tg-rss.git
cd tg-rss
```

### 4. Generate String Session (One-time, Local)

```bash
conda create -n tgrss python=3.11

conda activate tgrss

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_API_ID=your_api_id_here
export TELEGRAM_API_HASH=your_api_hash_here

# Generate session string
python scripts/generate_string_session.py
```

This will prompt for your phone number and verification code, then output a session string. Save this string - you'll need it for the next step.

### 5. Configure GitHub Repository Settings

#### Repository Permissions
Go to your repository's Settings → Actions → General:
1. Scroll down to "Workflow permissions"
2. Select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests" (optional)
4. Click "Save"

**Note:** If you forked this repository, make sure Actions are enabled in Settings → Actions → General.

#### Configure Secrets
Go to Settings → Secrets and variables → Actions, and add:

- `TELEGRAM_API_ID` - Your Telegram API ID
- `TELEGRAM_API_HASH` - Your Telegram API hash  
- `TELEGRAM_STRING_SESSION` - The session string from step 4
- (Optional) `GIT_USER_NAME` - Git commit author name
- (Optional) `GIT_USER_EMAIL` - Git commit author email

### 6. Configure Channels

Edit `channels.yml` to add the Telegram channels you want to follow:

```yaml
channels:
  - "@channel_1"
  - "@channel_2"
  - "@your_favorite_channel"
```

### 7. (Optional) Configure Keyword Filtering

Edit `keywords.yml` to filter posts by keywords (OR logic):

```yaml
keywords:
  - AI
  - LLM
  - blockchain
  - web3
```

Delete this file to disable filtering and include all posts.

### 8. Enable GitHub Pages

1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: / (root)
5. Click Save

### 9. Trigger First Run

Either:
- Push a commit to the main branch
- Go to Actions → "Telegram → RSS" → Run workflow
- Wait for the scheduled run (every 15 minutes)

## Usage

Once deployed, your RSS feed will be available at:

```
https://<your-github-username>.github.io/tg-rss/feed.xml
```

You can use this URL in any RSS reader or tool that accepts RSS feeds.

## Running Locally (Testing)

You can run the feed generator locally to test it before deploying:

### Setup Local Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_API_ID=your_api_id_here
export TELEGRAM_API_HASH=your_api_hash_here
export TELEGRAM_STRING_SESSION=your_session_string_here

# Optional: customize feed metadata
export FEED_TITLE="My Test Feed"
export FEED_LINK="https://example.com"
export FEED_DESC="Testing Telegram RSS"
export FEED_LIMIT=50
export FEED_DAYS=7  # Only fetch posts from last 7 days
```

### Run the Script

```bash
# Generate feed.xml in the current directory
python scripts/fetch_and_build_feed.py
```

This will:
1. Connect to Telegram using your session
2. Fetch messages from channels in `channels.yml`
3. Apply keyword filters from `keywords.yml` (if present)
4. Generate `feed.xml` in the project root
5. Update `state/last_ids.json` to track processed messages

### View the Generated Feed

```bash
# Check the generated RSS feed
cat feed.xml

# Or open in browser (macOS)
open feed.xml

# Or with any text editor
code feed.xml
```

### Test with Different Configurations

```bash
# Test without keyword filtering
mv keywords.yml keywords.yml.bak
python scripts/fetch_and_build_feed.py

# Test with specific channels
echo "channels: ['@telegram', '@durov']" > channels.yml
python scripts/fetch_and_build_feed.py

# Reset state to re-fetch all messages
echo "{}" > state/last_ids.json
python scripts/fetch_and_build_feed.py
```

### Validate RSS Feed

You can validate your generated RSS feed using online tools:
- https://validator.w3.org/feed/
- https://www.feedvalidator.org/

Simply paste the contents of your `feed.xml` file into these validators.

## Configuration

### Environment Variables (in GitHub Actions)

These can be customized in `.github/workflows/build.yml`:

- `FEED_TITLE` - RSS feed title (default: "Telegram Tech Aggregate")
- `FEED_LINK` - RSS feed link (default: "https://t.me")
- `FEED_DESC` - RSS feed description
- `FEED_LIMIT` - Maximum number of items in feed (default: 200)
- `FEED_DAYS` - Only include posts from last N days (default: 7)

### Update Frequency

The default schedule is every 15 minutes. To change this, edit the cron expression in `.github/workflows/build.yml`:

```yaml
schedule:
  - cron: "*/15 * * * *"  # Every 15 minutes
```

Common patterns:
- `"*/30 * * * *"` - Every 30 minutes
- `"0 * * * *"` - Every hour
- `"0 */6 * * *"` - Every 6 hours

## How It Works

1. **GitHub Actions** runs on schedule (every 15 minutes by default)
2. **Telethon** connects using your user session to read channel messages
3. **State tracking** ensures only new messages are fetched
4. **RSS builder** creates a valid RSS 2.0 feed
5. **Git commit** updates feed.xml and state
6. **GitHub Pages** automatically serves the updated feed

## Limitations

- Only works with public channels (or private ones you've joined)
- Telegram rate limits apply (handled gracefully with retries)
- GitHub Actions has monthly limits on free tier (2000 minutes)
- Feed limited to most recent N items (configurable)

## Troubleshooting

### GitHub Actions Permission Error

If you get "remote: Write access to repository not granted" error:

**Option 1: Use workflow permissions (Recommended)**
- Already added to the workflow file with `permissions: contents: write`

**Option 2: Repository settings**
1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Save changes

**Option 3: For forked repositories**
- Make sure Actions are enabled in your fork
- Check that the default branch is correct in the workflow file

### Session Expired

If the Telegram session expires, generate a new one and update the `TELEGRAM_STRING_SESSION` secret.

### Rate Limiting

If you hit Telegram rate limits, the script will automatically wait and retry. Consider reducing the number of channels or update frequency.

### Missing Posts

Check that:
- The channel is public or you've joined it
- Keywords (if configured) match the post content
- The post has text content (media-only posts need text/caption)
- Posts are within the FEED_DAYS limit (default: 7 days)

## Security Notes

- Never commit your API credentials or session string to the repository
- The session string provides full access to your Telegram account - keep it secure
- Use a dedicated Telegram account if concerned about security
- Regularly rotate your session string

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT

## Acknowledgments

Built with:
- [Telethon](https://github.com/LonamiWebs/Telethon) - Pure Python MTProto API Telegram client
- [PyYAML](https://github.com/yaml/pyyaml) - YAML parser and emitter
- GitHub Actions & GitHub Pages for free automation and hosting