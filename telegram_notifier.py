import telegram
import toml

config = toml.load('config.toml')
bot = telegram.Bot(token=config['bot']['token'])

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


