from datetime import date
from sqlmodel import create_engine, SQLModel, Field

sqlite_url = "sqlite:///db.sqlite3"

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str 
    dob: date

# create the engine
engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)