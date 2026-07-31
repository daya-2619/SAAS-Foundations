import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from .models import Project

import os
from confluent_kafka import Producer

# Setup Kafka Producer (Cached across requests)
kafka_broker = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
producer = Producer({"bootstrap.servers": kafka_broker})

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result """
    if err is not None:
        print(f"Message delivery failed: {err}")

@csrf_exempt
@require_POST
def ingest_logs_view(request):
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        return JsonResponse({"error": "Missing X-API-KEY header"}, status=401)
    
    try:
        project = Project.objects.get(api_key=api_key)
    except (Project.DoesNotExist, ValueError):
        return JsonResponse({"error": "Invalid API Key"}, status=401)
    
    try:
        data = json.loads(request.body)
        if not isinstance(data, list):
            data = [data]
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    produced_count = 0
    for item in data:
        # Add project_id so the consumer knows which project this belongs to
        item["project_id"] = str(project.id)
        
        # Asynchronously produce message to the 'incoming_logs' topic
        producer.produce(
            topic="incoming_logs",
            value=json.dumps(item).encode('utf-8'),
            callback=delivery_report
        )
        produced_count += 1
        
    # Serve delivery callback queue (wait for messages to be sent)
    producer.poll(0)
        
    return JsonResponse({"status": "ok", "inserted": produced_count, "method": "kafka"}, status=201)
