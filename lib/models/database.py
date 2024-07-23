from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# from dotenv import load_dotenv
# load_dotenv()

metadata = MetaData()

db = SQLAlchemy(metadata=metadata)
