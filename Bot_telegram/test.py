import os
import asyncio
import tempfile
from typing import Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import yt_dlp

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

# Maximum file size for Telegram (50MB)
MAX_FILE_SIZE = 49 * 1024 * 1024  # Slightly under 50MB to be safe

class VideoDownloader:
    def __init__(self):
        self.platforms = {
            "facebook": "facebook.com",
            "tiktok": "tiktok.com",
            "youtube": ("youtube.com", "youtu.be"),
        }

    def is_valid_url(self, url: str) -> bool:
        return any(platform in url.lower() if isinstance(platform, str) 
                  else any(p in url.lower() for p in platform) 
                  for platform in self.platforms.values())

    async def download_video(self, url: str, platform: str) -> Tuple[Optional[str], Optional[str]]:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_path = tmp_file.name

            # Basic options for all platforms
            ydl_opts = {
                'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b',  # Prefer MP4
                'merge_output_format': 'mp4',
                'outtmpl': tmp_path,
                'quiet': False,  # Enable output for debugging
                'no_warnings': False,
                'socket_timeout': 30,
                'retries': 10,
                'fragment_retries': 10,
                'restrictfilenames': True,
                'nooverwrites': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'geo_bypass': True,
            }

            if platform == 'youtube':
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4][filesize<49M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<49M]',
                    'prefer_ffmpeg': True,
                    'keepvideo': False,
                })
            elif platform == 'facebook':
                ydl_opts.update({
                    'format': 'best[ext=mp4][filesize<49M]',
                })
            elif platform == 'tiktok':
                ydl_opts.update({
                    'format': 'best[ext=mp4][filesize<49M]',
                })

            # Download the video
            async with asyncio.timeout(60):  # 60 seconds timeout
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
                )

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                file_size = os.path.getsize(tmp_path)
                if file_size <= MAX_FILE_SIZE:
                    return tmp_path, None
                else:
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return None, f"Video size ({file_size/1024/1024:.1f}MB) exceeds Telegram's limit (49MB)"
            return None, "Download failed: Empty file"
            
        except asyncio.TimeoutError:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return None, "Download timed out after 60 seconds"
        except Exception as e:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return None, f"Download error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("❓ How to Use", callback_data='how_to_use'),
            InlineKeyboardButton("ℹ️ About", callback_data='about')
        ],
        [
            InlineKeyboardButton("📢 Channel", url='https://e.me/@social_downlaoder_bot'),
            InlineKeyboardButton("👥 Support", url='https://t.me/Mondol_Real')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🎥 *Welcome to Social Media Video Downloader!*

I can help you download videos from:
• Facebook 📘
• TikTok 🎵
• YouTube 🎦

_Select an option below or send me a command:_
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'how_to_use':
        help_text = """
📝 *How to Use:*

Simply send one of these commands followed by the video URL:

/fb URL - Download Facebook video
/tk URL - Download TikTok video
/yt URL - Download YouTube video

Example:
`/yt https://youtube.com/watch?v=...`

⚠️ Maximum video size: 50MB
"""
        await query.message.edit_text(help_text, parse_mode='Markdown')
    
    elif query.data == 'about':
        about_text = """
ℹ️ *About This Bot*

• Fast downloads
• High quality videos
• Multiple platforms supported
• Regular updates
• 24/7 availability

Made with ❤️ by @your_username
"""
        await query.message.edit_text(about_text, parse_mode='Markdown')

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
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Flexible format selection
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

            # Add cookies for Facebook
            if platform == 'facebook':
                ydl_opts['cookies'] = 'cookies.txt'  # Path to your Facebook cookies file
                ydl_opts['format'] = 'best'  # Use the best available format for Facebook

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

async def download_facebook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'facebook')

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'tiktok')

async def download_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_and_send_video(update, context, 'youtube')

async def handle_invalid_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any non-command messages"""
    await update.message.reply_text(
        "❌ I only respond to commands. Please use one of these commands:\n"
        "/start - Start the bot\n"
        "/yt - Download YouTube video\n"
        "/tk - Download TikTok video\n"
        "/fb - Download Facebook video"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("fb", download_facebook))
    app.add_handler(CommandHandler("tk", download_tiktok))
    app.add_handler(CommandHandler("yt", download_youtube))
    
    # Add handler for all other types of messages (will be ignored)
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,  # Match all messages except commands
        handle_invalid_message
    ))
    
    # Set up commands before starting the bot
    asyncio.get_event_loop().run_until_complete(set_commands(app))
    
    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()