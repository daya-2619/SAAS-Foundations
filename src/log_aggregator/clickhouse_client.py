import os
import clickhouse_connect

def get_client():
    host = os.environ.get("CLICKHOUSE_HOST", "clickhouse")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
    try:
        client = clickhouse_connect.get_client(host=host, port=port, username='default', password='clickhouse')
        return client
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return None

def initialize_schema():
    client = get_client()
    if client:
        query = """
        CREATE TABLE IF NOT EXISTS log_entries (
            project_id Int64,
            timestamp DateTime64(3, 'UTC'),
            level LowCardinality(String),
            message String,
            raw_data String
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (project_id, timestamp)
        """
        client.command(query)
        print("ClickHouse schema initialized.")
        return True
    return False
