from langchain_community.graphs import Neo4jGraph
from app.config.settings import app_config

graph = Neo4jGraph(
    url=app_config.neo4j_url,
    username=app_config.neo4j_username,
    password=app_config.neo4j_password,
    driver_config={
        "max_connection_lifetime": 3600,
        "max_connection_pool_size": 20,
        "connection_acquisition_timeout": 30
    }
)

# fast api dependency in case we need to use it
async def get_graph() -> Neo4jGraph:
    return graph