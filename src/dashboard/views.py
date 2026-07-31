from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from log_aggregator.clickhouse_client import get_client
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import json
from log_aggregator.models import Project

def get_project_stats(project):
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    ch_client = get_client()
    project_id = str(project.id)
    
    total_24h = 0
    errors_24h = 0
    health_score = 100.0
    
    info_data = [0] * 60
    error_data = [0] * 60
    labels = []
    
    for i in range(60):
        t = one_hour_ago + timedelta(minutes=i)
        labels.append(t.strftime("%H:%M"))
        
    if ch_client:
        # KPIs
        twenty_four_hours_ago_str = twenty_four_hours_ago.strftime('%Y-%m-%d %H:%M:%S')
        kpi_query = f"SELECT count(), countIf(level = 'ERROR') FROM log_entries WHERE project_id = '{project_id}' AND timestamp >= '{twenty_four_hours_ago_str}'"
        kpi_result = ch_client.query(kpi_query)
        
        if kpi_result.result_rows:
            total_24h = kpi_result.result_rows[0][0]
            errors_24h = kpi_result.result_rows[0][1]
            
        if total_24h > 0:
            health_score = 100.0 - ((errors_24h / total_24h) * 100.0)
            
        # Chart
        one_hour_ago_str = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')
        chart_query = f"SELECT toStartOfMinute(timestamp) AS minute, level, count() FROM log_entries WHERE project_id = '{project_id}' AND timestamp >= '{one_hour_ago_str}' GROUP BY minute, level ORDER BY minute"
        chart_result = ch_client.query(chart_query)
        
        for row in chart_result.result_rows:
            minute_dt = row[0] # ClickHouse DateTime returns python datetime
            level = row[1]
            count = row[2]
            
            # ClickHouse might return naive datetime, make it aware for diff
            if minute_dt.tzinfo is None:
                minute_dt = minute_dt.replace(tzinfo=dt_timezone.utc)
                
            minute_diff = int((minute_dt - one_hour_ago).total_seconds() / 60)
            if 0 <= minute_diff < 60:
                if level == 'ERROR':
                    error_data[minute_diff] += count
                else:
                    info_data[minute_diff] += count
                    
    active_threats = project.alerts.filter(resolved=False).count()
                
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

@login_required
def dashboard_logs_api(request):
    projects = request.user.log_projects.all()
    q = request.GET.get('q', '').strip()
    
    ch_client = get_client()
    if not ch_client:
        return JsonResponse({"status": "error", "message": "ClickHouse unavailable"})
        
    data = {}
    for project in projects:
        project_id = str(project.id)
        
        query = f"SELECT timestamp, level, message FROM log_entries WHERE project_id = '{project_id}'"
        if q:
            safe_q = q.replace("'", "\\'")
            query += f" AND positionCaseInsensitive(message, '{safe_q}') > 0"
            
        query += " ORDER BY timestamp DESC LIMIT 50"
        
        try:
            result = ch_client.query(query)
            logs = []
            for row in result.result_rows:
                # ClickHouse returns python datetime
                logs.append({
                    'timestamp': row[0].strftime("%b %d, %H:%M:%S"),
                    'level': row[1],
                    'message': row[2]
                })
            data[project_id] = logs
        except Exception as e:
            data[project_id] = []
            
    return JsonResponse({"status": "ok", "data": data})

@login_required
def settings_view(request):
    return render(request, "dashboard/pages/settings.html", {"title": "Settings"})

@login_required
def kanban_view(request):
    return render(request, "dashboard/pages/kanban.html", {"title": "Kanban Board"})

@login_required
def calendar_view(request):
    return render(request, "dashboard/pages/calendar.html", {"title": "Calendar"})

@login_required
def products_view(request):
    return render(request, "dashboard/pages/products.html", {"title": "Products"})

@login_required
def invoice_view(request):
    return render(request, "dashboard/pages/invoice.html", {"title": "Invoices"})

@login_required
def messages_view(request):
    return render(request, "dashboard/pages/messages.html", {"title": "Messages"})

@login_required
def docs_view(request):
    return render(request, "dashboard/pages/docs.html", {"title": "Documentation"})

@login_required
def components_view(request):
    return render(request, "dashboard/pages/components.html", {"title": "Components"})

@login_required
def help_view(request):
    return render(request, "dashboard/pages/help.html", {"title": "Help Center"})