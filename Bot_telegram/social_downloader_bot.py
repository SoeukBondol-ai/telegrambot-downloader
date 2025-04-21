from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import yt_dlp
import os
import tempfile

# Replace with your Telegram bot token
TOKEN = "7886961216:AAE0Q5CJe7sgqibTjHyTDHOXaN3ADIwtJew"

# Define the commands and their descriptions
commands = [
    BotCommand("start", "Start the bot and show instructions"),
    BotCommand("yt", "Download a YouTube video"),
    BotCommand("tk", "Download a TikTok video"),
    BotCommand("fb", "Download a Facebook video"),
]

# Function to set bot commands
async def set_commands(application):
    """Set the bot commands."""
    await application.bot.set_my_commands(commands)

# Start command with interactive menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Create an inline keyboard with buttons
    keyboard = [
        [InlineKeyboardButton("📚 How to Use", callback_data="how_to_use")],
        [InlineKeyboardButton("📥 Download Video", callback_data="download_video")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/your_channel")],  # Replace with your channel link
        [InlineKeyboardButton("👥 Support", url="https://t.me/your_support")],  # Replace with your support link
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Welcome message
    welcome_text = """
    🎉 *Welcome to Social Downloader Bot!* 🎉

    I can help you download videos from:
    - YouTube 🎥
    - TikTok 🎵
    - Facebook 📘

    Click the buttons below to get started!
    """

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Callback handler for inline buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "how_to_use":
        await how_to_use(update, context)
    elif query.data == "download_video":
        await download_video_guide(update, context)

# How to Use guide
async def how_to_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = """
    📚 *How to Use the Bot:*

    1. To download a video, use one of these commands:
       - `/yt [YouTube URL]` - Download YouTube videos or shorts
       - `/tk [TikTok URL]` - Download TikTok videos
       - `/fb [Facebook URL]` - Download Facebook videos or reels

    2. Example:
       `/yt https://www.youtube.com/watch?v=example`

    3. The bot will process the video and send it to you.

    ⚠️ *Note:*
    - Ensure the URL is valid.
    - Videos larger than 50MB cannot be sent directly due to Telegram limits.
    """

    await update.callback_query.message.reply_text(
        guide_text,
        parse_mode="Markdown"
    )

# Download video guide
async def download_video_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = """
    📥 *Download Video:*

    Use one of these commands to download videos:
    - `/yt [YouTube URL]` - For YouTube videos
    - `/tk [TikTok URL]` - For TikTok videos
    - `/fb [Facebook URL]` - For Facebook videos

    Example:
    `/yt https://www.youtube.com/watch?v=example`
    """

    await update.callback_query.message.reply_text(
        guide_text,
        parse_mode="Markdown"
    )

# Video download function
async def download_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str):
    try:
        url = update.message.text.split(' ', 1)[1]
    except IndexError:
        await update.message.reply_text(f"⚠️ Please provide a {platform} URL after the command")
        return

    await update.message.reply_text("⏳ Starting download... Please wait!")

    try:
        # Create a temporary directory that will auto-delete
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',  # Limit to 1080p
                'merge_output_format': 'mp4',  # Force MP4 container
                'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',  # Convert to MP4
                    },
                    {
                        'key': 'FFmpegMetadata',  # Add metadata for better compatibility
                    },
                ],
                'C:/ffmpeg-master-latest-win64-gpl-shared/bin': 'ffmpeg',  # Ensure FFmpeg is used
            }

            if platform == 'facebook':
                ydl_opts['cookies'] = 'cookies.txt'  # Add your Facebook cookie file

            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                # Check file size
                file_size = os.path.getsize(filename)
                if file_size > 50 * 1024 * 1024:  # 50MB in bytes
                    await update.message.reply_text(
                        "⚠️ The video is too large to send directly (over 50MB).\n"
                        "Please use a service like WeTransfer or Google Drive."
                    )
                    return

                # Send the video to the user
                with open(filename, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"✅ Here's your {platform.capitalize()} video!"
                    )

        # The temporary directory and its files are automatically deleted here

    except Exception as e:
        await update.message.reply_text(f"❌ Error downloading video: {str(e)}")

# Command handlers for downloading videos
async def download_facebook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'facebook')

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'tiktok')

async def download_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'youtube')

# Main function to start the bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yt", download_youtube))
    app.add_handler(CommandHandler("tk", download_tiktok))
    app.add_handler(CommandHandler("fb", download_facebook))

    # Add callback query handler for inline buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Set up command suggestions manually
    app.run_polling()

    # Manually set commands after the bot starts
    app.bot.set_my_commands(commands)

if __name__ == "__main__":
    main()