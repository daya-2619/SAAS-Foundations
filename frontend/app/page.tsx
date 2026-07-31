"use client";

import React, { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Activity, AlertTriangle, ShieldCheck, Search } from "lucide-react";

interface KPIData {
  total_24h: number;
  health_score: string;
  active_threats: number;
}

interface ChartData {
  labels: string[];
  info_data: number[];
  error_data: number[];
}

interface AlertData {
  timestamp: string;
  description: string;
}

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export default function Dashboard() {
  const [statsData, setStatsData] = useState<any>(null);
  const [logsData, setLogsData] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("/api/dashboard/stats/");
        const json = await res.json();
        if (json.status === "ok") {
          setStatsData(json.data);
        }
      } catch (e) {
        console.error("Failed to fetch stats", e);
      }
    };

    fetchStats();
    const statsInterval = setInterval(fetchStats, 5000);
    return () => clearInterval(statsInterval);
  }, []);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const url = new URL(window.location.origin + "/api/dashboard/logs/");
        if (searchQuery) {
          url.searchParams.append("q", searchQuery);
        }
        const res = await fetch(url.toString());
        const json = await res.json();
        if (json.status === "ok") {
          setLogsData(json.data);
        }
      } catch (e) {
        console.error("Failed to fetch logs", e);
      }
    };

    fetchLogs();
    const logsInterval = setInterval(fetchLogs, 3000);
    return () => clearInterval(logsInterval);
  }, [searchQuery]);

  if (!statsData) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-slate-500 animate-pulse text-lg font-medium">Loading Dashboard Data...</div>
      </div>
    );
  }

  // Assuming single project for simplicity in the SPA
  const projectId = Object.keys(statsData)[0];
  if (!projectId) return <div className="p-8">No projects found.</div>;

  const projectStats = statsData[projectId];
  const projectLogs = logsData ? logsData[projectId] || [] : [];
  
  const chartOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#334155' },
      padding: [12, 16],
      borderRadius: 12,
      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)'
    },
    legend: {
      data: ['Normal Traffic', 'Anomalies'],
      bottom: 0,
      icon: 'circle',
      textStyle: { color: '#64748b' }
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '12%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: projectStats.chart.labels,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: 'Normal Traffic',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#6366f1' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
              { offset: 1, color: 'rgba(99, 102, 241, 0.05)' }
            ]
          }
        },
        data: projectStats.chart.info_data
      },
      {
        name: 'Anomalies',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#ef4444' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
            ]
          }
        },
        data: projectStats.chart.error_data
      }
    ]
  };

  const highlightText = (text: string, highlight: string) => {
    if (!highlight.trim()) return text;
    const parts = text.split(new RegExp(`(${highlight})`, 'gi'));
    return (
      <span>
        {parts.map((part, i) => 
          part.toLowerCase() === highlight.toLowerCase() ? (
            <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-1">{part}</mark>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Security Command Center</h1>
            <p className="text-slate-500 mt-1">Real-time observability and threat detection.</p>
          </div>
          <div className="mt-4 md:mt-0 flex space-x-3">
            <button className="bg-white border border-slate-200 text-slate-700 px-4 py-2 rounded-xl text-sm font-medium hover:bg-slate-50 transition-colors shadow-sm">
              Export Report
            </button>
            <button className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200">
              Settings
            </button>
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center justify-between group hover:border-indigo-200 transition-colors">
            <div>
              <p className="text-sm font-semibold text-slate-500 tracking-wide uppercase">Ingested Logs (24h)</p>
              <h3 className="text-3xl font-black text-slate-800 mt-2">{projectStats.kpi.total_24h.toLocaleString()}</h3>
            </div>
            <div className="bg-indigo-50 p-4 rounded-2xl group-hover:bg-indigo-100 transition-colors">
              <Activity className="w-8 h-8 text-indigo-600" />
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center justify-between group hover:border-emerald-200 transition-colors">
            <div>
              <p className="text-sm font-semibold text-slate-500 tracking-wide uppercase">System Health</p>
              <h3 className="text-3xl font-black text-emerald-600 mt-2">{projectStats.kpi.health_score}</h3>
            </div>
            <div className="bg-emerald-50 p-4 rounded-2xl group-hover:bg-emerald-100 transition-colors">
              <ShieldCheck className="w-8 h-8 text-emerald-600" />
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex items-center justify-between group hover:border-rose-200 transition-colors">
            <div>
              <p className="text-sm font-semibold text-slate-500 tracking-wide uppercase">Active Threats</p>
              <h3 className="text-3xl font-black text-rose-600 mt-2">{projectStats.kpi.active_threats}</h3>
            </div>
            <div className="bg-rose-50 p-4 rounded-2xl group-hover:bg-rose-100 transition-colors">
              <AlertTriangle className="w-8 h-8 text-rose-600" />
            </div>
          </div>
        </div>

        {/* Chart Section */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <h4 className="text-lg font-bold text-slate-800 mb-6">Traffic & Anomaly Trend (Last 60 Minutes)</h4>
          <ReactECharts option={chartOption} style={{ height: "400px" }} />
        </div>

        {/* Anomalies Section */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-lg font-bold text-slate-800">Recent Anomalies</h4>
            <span className="bg-rose-100 text-rose-600 py-1 px-3 rounded-full text-xs font-bold tracking-widest uppercase">
              {projectStats.alerts?.length || 0}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projectStats.alerts && projectStats.alerts.length > 0 ? (
              projectStats.alerts.map((alert: any, i: number) => (
                <div key={i} className="bg-rose-50 border border-rose-100 rounded-xl p-4 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <p className="text-sm text-rose-900 font-medium mb-3">{alert.description}</p>
                  <p className="text-xs text-rose-400 font-bold uppercase tracking-wider">{alert.timestamp}</p>
                </div>
              ))
            ) : (
              <div className="text-slate-500 py-4 col-span-3">No recent threats detected.</div>
            )}
          </div>
        </div>

        {/* Live Log Stream */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
            <div className="flex items-center space-x-3">
              <h4 className="text-lg font-bold text-slate-800">Live Log Stream</h4>
              <div className="flex items-center space-x-2 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
                <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-widest">Tailing</span>
              </div>
            </div>
            <div className="relative w-full md:w-96">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-slate-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search logs (e.g. timeout, 500)..."
                className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors"
              />
            </div>
          </div>
          
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-widest w-48">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-widest w-24">Level</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">Message</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100 font-mono text-sm">
                {projectLogs.length > 0 ? (
                  projectLogs.map((log: LogEntry, idx: number) => {
                    let levelClass = "text-slate-500 bg-slate-100";
                    if (log.level === 'ERROR') levelClass = "text-rose-600 bg-rose-100";
                    else if (log.level === 'WARNING') levelClass = "text-amber-600 bg-amber-100";
                    else if (log.level === 'INFO') levelClass = "text-indigo-600 bg-indigo-50";

                    return (
                      <tr key={idx} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-3 whitespace-nowrap text-slate-500 text-xs">{log.timestamp}</td>
                        <td className="px-6 py-3 whitespace-nowrap">
                          <span className={`px-2.5 py-1 inline-flex text-[10px] leading-5 font-bold rounded-md uppercase tracking-wider ${levelClass}`}>
                            {log.level}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-700 truncate max-w-2xl">
                          {highlightText(log.message, searchQuery)}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={3} className="px-6 py-8 text-center text-slate-500 font-sans">
                      {logsData ? "No logs found matching your criteria." : "Connecting to stream..."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        
      </div>
    </div>
  );
}
