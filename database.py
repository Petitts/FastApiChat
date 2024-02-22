from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["teleinformatyka_projekt"]