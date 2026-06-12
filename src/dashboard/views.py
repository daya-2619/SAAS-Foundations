from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.utils import timezone
from datetime import timedelta
import json
from log_aggregator.models import Project

def get_project_stats(project):
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # KPIs
    total_24h = project.logs.filter(timestamp__gte=twenty_four_hours_ago).count()
    errors_24h = project.logs.filter(level='ERROR', timestamp__gte=twenty_four_hours_ago).count()
    health_score = 100.0
    if total_24h > 0:
        health_score = 100.0 - ((errors_24h / total_24h) * 100.0)
    
    active_threats = project.alerts.filter(resolved=False).count()
    
    # Chart
    logs = project.logs.filter(timestamp__gte=one_hour_ago).annotate(
        minute=TruncMinute('timestamp')
    ).values('minute', 'level').annotate(count=Count('id')).order_by('minute')
    
    info_data = [0] * 60
    error_data = [0] * 60
    labels = []
    
    for i in range(60):
        t = one_hour_ago + timedelta(minutes=i)
        labels.append(t.strftime("%H:%M"))
        
    for log in logs:
        if not log['minute']: continue
        minute_diff = int((log['minute'] - one_hour_ago).total_seconds() / 60)
        if 0 <= minute_diff < 60:
            if log['level'] == 'ERROR':
                error_data[minute_diff] += log['count']
            else:
                info_data[minute_diff] += log['count']
                
    # Latest Alerts
    recent_alerts = []
    for alert in project.alerts.filter(resolved=False)[:5]:
        recent_alerts.append({
            'timestamp': alert.timestamp.strftime("%b %d, %Y %H:%M:%S"),
            'description': alert.description
        })

    return {
        'kpi': {
            'total_24h': total_24h,
            'health_score': f"{health_score:.1f}%",
            'active_threats': active_threats,
        },
        'chart': {
            'labels': labels,
            'info_data': info_data,
            'error_data': error_data
        },
        'alerts': recent_alerts
    }

@login_required
def dashboard_view(request):
    if not request.user.log_projects.exists():
        Project.objects.create(user=request.user, name="My Primary Application")
        
    projects = request.user.log_projects.prefetch_related('alerts').all()
    
    chart_data = {}
    kpi_data = {}
    
    for project in projects:
        stats = get_project_stats(project)
        chart_data[str(project.id)] = stats['chart']
        kpi_data[str(project.id)] = stats['kpi']

    context = {
        "projects": projects,
        "chart_data_json": json.dumps(chart_data),
        "kpi_data": kpi_data,
    }
    return render(request, "dashboard/main.html", context)

@login_required
def dashboard_stats_api(request):
    projects = request.user.log_projects.all()
    data = {}
    for project in projects:
        data[str(project.id)] = get_project_stats(project)
    return JsonResponse({"status": "ok", "data": data})