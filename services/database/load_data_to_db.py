# define database connection
import os

import pandas as pd
from config import db_config
from sqlalchemy import create_engine, text
from sqlalchemy.types import Integer, Text

DATA_FOLDER = "./cleaned_resources"


# function to identify primary key
def identify_primary_key(df):
    for col in df.columns:
        if df[col].is_unique and not df[col].isnull().any():
            return col
    return None


def setup_primary_keys(engine, pk_map):
    with engine.connect() as conn:
        for table_name, pk_column in pk_map.items():
            try:
                sql = f"""
                ALTER TABLE {table_name} 
                ADD PRIMARY KEY ({pk_column});
                """
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Set PRIMARY KEY on {table_name}.{pk_column}")
            except Exception as e:
                print(f"⚠️ Could not set PK on {table_name}.{pk_column}: {e}")


def setup_foreign_keys(engine, pk_map):
    relationships = []

    # Scan all tables to find foreign keys
    for file in os.listdir(DATA_FOLDER):
        if not file.endswith(".csv"):
            continue

        child_table = os.path.splitext(file)[0]
        df = pd.read_csv(os.path.join(DATA_FOLDER, file))

        # Check each column to see if it matches a primary key from another table
        for col in df.columns:
            for parent_table, parent_pk in pk_map.items():
                if child_table == parent_table:
                    continue  # Skip self-reference

                if col == parent_pk:
                    relationships.append((child_table, col, parent_table, parent_pk))

    # Create foreign key
    with engine.connect() as conn:
        for child_table, child_col, parent_table, parent_col in relationships:
            sql = f"""
                ALTER TABLE {child_table} 
                ADD CONSTRAINT fk_{child_table}_{child_col} 
                FOREIGN KEY ({child_col}) REFERENCES {parent_table} ({parent_col});
                """
            conn.execute(text(sql))
            conn.commit()
            print(f"✅ Linked {child_table}.{child_col} -> {parent_table}.{parent_col}")


def load_data():
    DB_URI = db_config.DATABASE_URI()
    engine = create_engine(DB_URI)

    if not os.path.exists(DATA_FOLDER):
        print("Creating folder...")
        os.makedirs(DATA_FOLDER)
        return

    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    print(f"👌 Found {len(csv_files)} files.\n")

    # Store primary key info for foreign key setup
    pk_map = {}  # {table_name: pk_column_name}

    for file_name in csv_files:
        table_name = os.path.splitext(file_name)[0]
        file_path = os.path.join(DATA_FOLDER, file_name)

        try:
            df = pd.read_csv(file_path)
            # Find primary key
            pk_column = identify_primary_key(df)
            dtype_dict = {}

            if pk_column:
                if df[pk_column].dtype == "int64":
                    dtype_dict[pk_column] = Integer()
                else:
                    dtype_dict[pk_column] = Text()

                pk_map[table_name] = pk_column
                print(f"🔹 '{table_name}': Found PK column '{pk_column}'.")
            else:
                print(f"⚠️ '{table_name}': No primary key found.")

            df.to_sql(
                table_name,
                engine,
                if_exists="replace",
                index=False,
                dtype=dtype_dict,
            )
            print(f"✅ Uploaded '{table_name}' ({len(df)} rows)")

        except Exception as e:
            print(f"❌ Error uploading {file_name}: {e}")

    print("\n🔑 Setting up Primary Keys...")
    setup_primary_keys(engine, pk_map)

    print("\n🔗 Setting up Foreign Keys...")
    setup_foreign_keys(engine, pk_map)

    print("\n🎉 All operations completed.")


if __name__ == "__main__":
    load_data()
