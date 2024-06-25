import telegram

bot = telegram.Bot(token='')

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


