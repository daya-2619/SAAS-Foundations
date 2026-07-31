import os
import json
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from confluent_kafka import Consumer, KafkaError
from log_aggregator.models import Project
from log_aggregator.clickhouse_client import get_client, initialize_schema

class Command(BaseCommand):
    help = 'Consume logs from Kafka and batch insert into PostgreSQL'

    def handle(self, *args, **options):
        kafka_broker = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
        
        c = Consumer({
            'bootstrap.servers': kafka_broker,
            'group.id': 'logcenter_db_writer',
            'auto.offset.reset': 'earliest'
        })
        
        c.subscribe(['incoming_logs'])
        
        self.stdout.write(self.style.SUCCESS(f'Started consuming from {kafka_broker}'))
        
        initialize_schema()
        ch_client = get_client()
        if not ch_client:
            self.stderr.write("FATAL: Could not connect to ClickHouse")
            return

        batch = []
        BATCH_SIZE = 500
        
        # Simple project cache to avoid DB hits
        project_cache = {}

        try:
            while True:
                msg = c.poll(1.0)
                
                if msg is None:
                    # Flush batch if there are messages waiting and no new ones
                    if batch:
                        ch_client.insert('log_entries', batch, column_names=['project_id', 'timestamp', 'level', 'message', 'raw_data'])
                        self.stdout.write(f'Inserted batch of {len(batch)} logs to ClickHouse')
                        batch = []
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        self.stderr.write(f'Kafka Error: {msg.error()}')
                        break
                        
                # Parse message
                try:
                    data = json.loads(msg.value().decode('utf-8'))
                    
                    project_id = data.get("project_id")
                    if project_id not in project_cache:
                        project_cache[project_id] = Project.objects.get(id=project_id)
                    
                    project = project_cache[project_id]
                    timestamp_str = data.get("timestamp")
                    level = data.get("level", "INFO")
                    message = data.get("message", "")
                    raw_data = data.get("raw_data", None)
                    
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                        if timestamp:
                            batch.append([
                                project.id,
                                timestamp.replace(tzinfo=None), # ClickHouse expects naive datetime for UTC or handled correctly
                                level,
                                message,
                                json.dumps(raw_data) if raw_data else "{}"
                            ])
                            
                except Exception as e:
                    self.stderr.write(f'Error processing message: {e}')
                    
                if len(batch) >= BATCH_SIZE:
                    ch_client.insert('log_entries', batch, column_names=['project_id', 'timestamp', 'level', 'message', 'raw_data'])
                    self.stdout.write(f'Inserted batch of {len(batch)} logs to ClickHouse')
                    batch = []
                    
        except KeyboardInterrupt:
            pass
        finally:
            # Flush any remaining logs
            if batch:
                ch_client.insert('log_entries', batch, column_names=['project_id', 'timestamp', 'level', 'message', 'raw_data'])
                self.stdout.write(f'Inserted final batch of {len(batch)} logs to ClickHouse')
            c.close()
