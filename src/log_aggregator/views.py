import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from .models import Project, LogEntry

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
    
    log_entries = []
    for item in data:
        timestamp_str = item.get("timestamp")
        level = item.get("level", "INFO")
        message = item.get("message", "")
        raw_data = item.get("raw_data", None)
        
        if not timestamp_str:
            continue
            
        timestamp = parse_datetime(timestamp_str)
        if not timestamp:
            continue
            
        log_entries.append(
            LogEntry(
                project=project,
                timestamp=timestamp,
                level=level,
                message=message,
                raw_data=raw_data
            )
        )
        
    if log_entries:
        LogEntry.objects.bulk_create(log_entries, batch_size=1000)
        
    return JsonResponse({"status": "ok", "inserted": len(log_entries)}, status=201)
