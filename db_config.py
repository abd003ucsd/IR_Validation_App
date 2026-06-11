import json
import os
import pandas as pd
from typing import Optional
from sqlalchemy import create_engine

# Load Config
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(config_path, 'r') as f:
        _config = json.load(f)
except Exception:
    _config = {}

DEFAULT_SERVER = _config.get("DEFAULT_SERVER", "localhost")
IR_DB_PRESETS = _config.get("IR_DB_PRESETS", {"Other": "Other"})

def run_db_query(
    server: str,
    database: str,
    query: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_windows_auth: bool = True
) -> pd.DataFrame:
    """
    Execute a SQL query and return a DataFrame.
    Supports Windows and SQL Authentication.
    """
    if use_windows_auth:
        conn_str = (
            f"mssql+pyodbc://@{server}/{database}"
            "?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
        )
    else:
        conn_str = (
            f"mssql+pyodbc://{username}:{password}@{server}/{database}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )

    # Use a short timeout for the connection attempt
    engine = create_engine(conn_str, connect_args={'timeout': 10})
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
        return df
    finally:
        engine.dispose()
