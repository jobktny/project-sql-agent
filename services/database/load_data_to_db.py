import os
import pandas as pd
from sqlalchemy import create_engine
from config import db_config

# define database connection
DB_URI = db_config.DATABASE_URI()
DATA_FOLDER = './cleaned_resources'

engine = create_engine(DB_URI)

# function to identify primary key for each table
def identify_primary_key(df):
    for col in df.columns:
        if df[col].is_unique and not df[col].isnull().any():
            return col
    return None


## TODO not yet done need to make it simpler and I need to understand

