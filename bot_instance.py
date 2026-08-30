"""Single shared Client instance; kept in its own module to avoid import cycles."""

from balethon import Client
from config import TOKEN

bot = Client(token=TOKEN)