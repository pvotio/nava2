import logging
import time

import pandas as pd

logger = logging.getLogger(__name__)


class DBAdapter:
    def __init__(self, db):
        self.db = db

    def read_sql(self, query, params=None, none_on_empty_df=False):
        for _ in range(3):
            try:
                df = pd.read_sql_query(query, self.db.conn, params=params)
                if df.empty and none_on_empty_df:
                    return None
                return df
            except Exception as e:
                logger.error(f"Error executing query: {e}", exc_info=True)
                time.sleep(0.5)
        raise RuntimeError("Failed to execute query after 3 attempts.")

    def is_record_exist(self, query, params=None):
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result is not None
