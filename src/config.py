import os
from dotenv import load_dotenv

load_dotenv()
# MongoDB connection URI
uri = os.getenv('MongoDB_URI')
