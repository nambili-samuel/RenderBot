# =========================================================
# MAIN (WEBHOOK MODE — RENDER SAFE)
# =========================================================
def main():
    logger.info("=" * 60)
    logger.info("🇳🇦 EVA GEISES - NAMIBIA EXPERT (WEBHOOK MODE)")
    logger.info("=" * 60)

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    BASE_URL = os.getenv("WEBHOOK_URL")  # https://renderbot-x64y.onrender.com
    PORT = int(os.getenv("PORT", "10000"))

    if not TELEGRAM_BOT_TOKEN or not BASE_URL:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or WEBHOOK_URL")

    WEBHOOK_PATH = "webhook"
    FULL_WEBHOOK_URL = f"{BASE_URL}/{WEBHOOK_PATH}"

    logger.info(f"🌐 Webhook URL: {FULL_WEBHOOK_URL}")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(20)
        .read_timeout(20)
        .write_timeout(20)
        .build()
    )

    # ================= HANDLERS =================
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('properties', properties_command))
    app.add_handler(CommandHandler('topics', topics_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('add', add_command))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members))

    # IMPORTANT: do NOT catch commands here
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, handle_group_message)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, handle_private_message)
    )

    # ================= SCHEDULED JOBS =================
    job_queue = app.job_queue

    job_queue.run_daily(
        post_daily_property,
        time=datetime.strptime("10:00", "%H:%M").time(),
        name="daily_property_post"
    )

    job_queue.run_repeating(
        send_periodic_greetings,
        interval=7200,
        first=300,
        name="periodic_greetings"
    )

    logger.info("🚀 Eva is running via WEBHOOK (no polling)")
    logger.info("📅 Daily property posts enabled")
    logger.info("👋 Periodic greetings enabled")

    # ================= WEBHOOK =================
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=FULL_WEBHOOK_URL,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
