from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import settings

mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
connection = mongo_client[settings.MONGODB_DATABASE]
