import duckdb
from app.config.settings import app_config
from loguru import logger
from typing import Dict, List, Any, Tuple, Optional
from app.utils.decorators import log_errors


class AnalyticsProvider:

    def __init__(self):
        self.motherduck_url = app_config.motherduck_url

    @log_errors
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.motherduck_url)
    
    @log_errors
    def sql(
        self,
        query: str, 
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            return (
                conn.execute(query, params)
                    .fetch_df()
                    .to_dict('records')
            )
