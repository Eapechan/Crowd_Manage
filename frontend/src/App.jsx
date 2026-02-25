import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Users,
  Activity,
  TrendingUp,
  AlertTriangle,
  Settings,
  Coffee,
  ShoppingBag,
  Calendar,
  Zap,
  Play,
  Square
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

const API_BASE = "http://localhost:8000";

const App = () => {
  const [stats, setStats] = useState({
    count: 0,
    density: "LOW",
    alert: false,
    peak_count: 0,
    fps: 0,
    mode: "canteen"
  });
  const [history, setHistory] = useState([]);
  const [isLive, setIsLive] = useState(true);

  const historyRef = useRef([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);

      const newPoint = {
        time: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        count: data.count
      };

      historyRef.current = [...historyRef.current, newPoint].slice(-30);
      setHistory(historyRef.current);
    };

    return () => ws.close();
  }, []);

  const changeMode = async (mode) => {
    try {
      await axios.post(`${API_BASE}/config`, { mode });
    } catch (error) {
      console.error("Failed to change mode:", error);
    }
  };

  const getThemeConfig = () => {
    switch (stats.mode) {
      case 'canteen':
        return {
          name: "Foodie Dashboard",
          mainLabel: "Kitchen Load",
          subLabel: "Dining Tables Availability",
          icon: <Coffee size={28} color="#FF7F50" />,
          bgColor: "theme-canteen",
          accent: "#FF7F50"
        };
      case 'shop':
        return {
          name: "Store Tracker",
          mainLabel: "Store Traffic",
          subLabel: "Customer Movement",
          icon: <ShoppingBag size={28} color="#008080" />,
          bgColor: "theme-shop",
          accent: "#008080"
        };
      case 'event':
      default:
        return {
          name: "Safety Control",
          mainLabel: "Crowd Density",
          subLabel: "Arena Capacity",
          icon: <Activity size={28} color="#E74C3C" />,
          bgColor: "theme-event",
          accent: "#E74C3C"
        };
    }
  };

  const theme = getThemeConfig();

  return (
    <div className={`dashboard-container ${theme.bgColor}`}>
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {theme.icon}
          <div>
            <h1 style={{ fontSize: '1.25rem' }}>{theme.name}</h1>
            <p className="stat-label" style={{ fontSize: '0.65rem' }}>Crowd Control AI System</p>
          </div>
        </div>
        <div className="status-indicator">
          <div className="dot" style={{ backgroundColor: isLive ? 'var(--accent-green)' : '#999' }}></div>
          {isLive ? "LIVE DATA STREAM" : "OFFLINE"}
        </div>
      </header>

      <aside>
        <div className="sidebar-logo">CROWD AI</div>

        <div className="mode-selector">
          <p className="stat-label">Select Mode</p>
          <button
            className={`mode-btn ${stats.mode === 'canteen' ? 'active' : ''}`}
            onClick={() => changeMode('canteen')}
          >
            <Coffee size={18} /> Canteen
          </button>
          <button
            className={`mode-btn ${stats.mode === 'shop' ? 'active' : ''}`}
            onClick={() => changeMode('shop')}
          >
            <ShoppingBag size={18} /> Retail Shop
          </button>
          <button
            className={`mode-btn ${stats.mode === 'event' ? 'active' : ''}`}
            onClick={() => changeMode('event')}
          >
            <Calendar size={18} /> Event Arena
          </button>
        </div>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button
            className="mode-btn"
            style={{
              backgroundColor: isLive ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)',
              borderColor: isLive ? 'var(--accent-red)' : 'var(--accent-green)'
            }}
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Square size={18} /> : <Play size={18} />}
            {isLive ? "Pause" : "Resume"}
          </button>
        </div>
      </aside>

      <main>
        {stats.alert && (
          <div className="alert-panel active pulse-red">
            <AlertTriangle size={24} />
            <div>
              <strong>HIGH DENSITY ALERT!</strong>
              <p style={{ fontSize: '0.8rem', opacity: 0.9 }}>Capacity exceeded. Take action!</p>
            </div>
          </div>
        )}

        <div className="metrics-grid">
          <div className="card">
            <div className="stat-label">{theme.mainLabel}</div>
            <div className="stat-value" style={{ color: theme.accent }}>
              {stats.count}
            </div>
            <div className="stat-label" style={{ fontSize: '0.7rem' }}>People Detected</div>
          </div>

          <div className="card">
            <div className="stat-label">Status</div>
            <div className="stat-value">
              {stats.density}
            </div>
            <div className="stat-label" style={{ fontSize: '0.7rem' }}>Current Flow</div>
          </div>

          <div className="card">
            <div className="stat-label">Peak Efficiency</div>
            <div className="stat-value">
              {stats.peak_count}
            </div>
            <div className="stat-label" style={{ fontSize: '0.7rem' }}>Highest Recorded</div>
          </div>

          <div className="card">
            <div className="stat-label">System Pulse</div>
            <div className="stat-value" style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              {stats.fps} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>FPS</span>
            </div>
            <div className="stat-label" style={{ fontSize: '0.7rem' }}>Processing Speed</div>
          </div>
        </div>

        <div className="content-grid">
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <div className="stat-label" style={{ padding: '1rem 1.5rem' }}>Visual Feed</div>
            <div className="video-section">
              {isLive ? (
                <img
                  src={`${API_BASE}/video?t=${Date.now()}`}
                  alt="Live Feed"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  onError={(e) => {
                    e.target.src = "https://via.placeholder.com/640x480/0D1117/333?text=Stream+Disconnected";
                  }}
                />
              ) : (
                <div style={{ color: 'var(--text-muted)' }}>Monitoring Paused</div>
              )}
            </div>
          </div>

          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="stat-label">{theme.subLabel}</div>

            {stats.mode === 'shop' ? (
              <div className="avatar-container">
                {Array.from({ length: stats.count }).map((_, i) => (
                  <Users key={i} size={24} className="avatar-icon" color={theme.accent} />
                ))}
                {stats.count === 0 && <p className="stat-label">No customers yet...</p>}
              </div>
            ) : (
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={theme.accent} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={theme.accent} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363D" vertical={false} />
                    <XAxis dataKey="time" hide />
                    <YAxis hide domain={[0, 'auto']} />
                    <Tooltip contentStyle={{ background: '#161B22', border: 'none', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="count" stroke={theme.accent} fill="url(#colorCount)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <p className="stat-label">AI Accuracy Engine</p>
                <Zap size={16} color="var(--accent-orange)" />
              </div>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Filters: Class-0, Conf{'>'}0.6, Area{'>'}0.2%, Stability{'>'}3f
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
