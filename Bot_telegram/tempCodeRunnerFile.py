def main():
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("fb", download_facebook))
    app.add_handler(CommandHandler("tk", download_tiktok))
    app.add_handler(CommandHandler("yt", download_youtube))
    
    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)