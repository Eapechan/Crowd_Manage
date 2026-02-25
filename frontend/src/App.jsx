import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Activity,
  Users,
  Clock,
  AlertTriangle,
  ShoppingBag,
  Coffee,
  Square,
  Play,
  Zap,
  ChevronRight,
  MapPin
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

const App = () => {
  const [stats, setStats] = useState({
    count: 0,
    density: "LOW",
    alert: false,
    peak_count: 0,
    fps: 0,
    mode: "canteen",
    wait_time: 0,
    message: "Welcome",
    availability: "Checking..."
  });
  const [isLive, setIsLive] = useState(true);
  const [streamError, setStreamError] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);
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
          subLabel: "Cafe Activity",
          icon: <Coffee size={28} color="#FF7F50" />,
          bgColor: "theme-canteen",
          accent: "#FF7F50",
          gamifiedContent: (
            <div className="gamified-panel">
              <div className="card-sub-header">DINING EXPERIENCE</div>
              <div className="menu-list">
                <div className="menu-item"><span>🍕 Spicy Salami</span> <span>$12</span></div>
                <div className="menu-item"><span>🍔 Classic Beef</span> <span>$14</span></div>
                <div className="menu-item" style={{ opacity: 0.4 }}><span>🥗 Caesar (Sold Out)</span> <Zap size={12} color="#999" /></div>
              </div>
              <div className="wait-info">
                <Clock size={16} /> Est. Wait Time: {stats.wait_time} mins
              </div>
              <button className="mode-btn" style={{ borderStyle: 'dashed', borderColor: '#FF7F50', color: '#FF7F50' }}>
                VIEW FULL MENU <ChevronRight size={14} />
              </button>
            </div>
          )
        };
      case 'shop':
        return {
          name: "Retail Analytics",
          mainLabel: "Traffic",
          subLabel: "Customer Insights",
          icon: <ShoppingBag size={28} color="#008080" />,
          bgColor: "theme-shop",
          accent: "#008080",
          gamifiedContent: (
            <div className="gamified-panel">
              <div className="analytics-box">
                <div className="card-sub-header">ZONE FLOW</div>
                <div className="zone-bar">
                  <span>Entrance Path</span>
                  <div className="bar-bg"><div className="bar-fill" style={{ width: `${Math.min(stats.count * 10, 100)}%`, background: '#008080' }}></div></div>
                </div>
                <div className="zone-bar">
                  <span>Checkout Line</span>
                  <div className="bar-bg"><div className="bar-fill" style={{ width: '25%', background: '#2ECC71' }}></div></div>
                </div>
              </div>
              <div className="avatar-grid">
                {Array.from({ length: Math.min(stats.count, 24) }).map((_, i) => (
                  <Users key={i} size={18} className="avatar-icon" color="#008080" />
                ))}
              </div>
              <div className="ai-tag" style={{ display: 'flex', alignItems: 'center', gap: '5px', width: 'fit-content' }}>
                <MapPin size={10} /> Peak: Saturday
              </div>
            </div>
          )
        };
      case 'event':
      default:
        return {
          name: "Safety Control",
          mainLabel: "Arena Density",
          subLabel: "Security Protocols",
          icon: <Activity size={28} color="#E74C3C" />,
          bgColor: "theme-event",
          accent: "#E74C3C",
          gamifiedContent: (
            <div className="gamified-panel">
              <div className="emergency-alert">
                <AlertTriangle size={18} /> EMERGENCY EXIT PLAN
                <div className="map-placeholder">
                  [ FLOOR 1 ENTRANCE ]
                </div>
              </div>
              <div className="status-indicator" style={{ marginTop: 'auto' }}>
                <div className="dot" style={{ background: '#2ECC71' }}></div>
                <span>Gate 1: NORMAL</span>
              </div>
              <div className="status-indicator">
                <div className="dot" style={{ background: stats.alert ? '#E74C3C' : '#2ECC71' }}></div>
                <span>Gate 2: {stats.alert ? 'CONGESTED' : 'CLEAR'}</span>
              </div>
            </div>
          )
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
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800 }}>{theme.name}</h1>
            <p className="stat-label" style={{ fontSize: '0.65rem' }}>{stats.message}</p>
          </div>
        </div>
        <div className="status-indicator">
          <div className="dot" style={{ backgroundColor: isLive ? '#2ECC71' : '#E74C3C' }}></div>
          {isLive ? "MONITORING ACTIVE" : "SYSTEM PAUSED"}
        </div>
      </header>

      <aside>
        <div className="sidebar-logo">CROWD CONTROL</div>
        <div className="mode-selector">
          <p className="stat-label">OPERATIONS</p>
          <button className={`mode-btn ${stats.mode === 'canteen' ? 'active' : ''}`} onClick={() => changeMode('canteen')}>
            <Coffee size={18} /> Canteen View
          </button>
          <button className={`mode-btn ${stats.mode === 'shop' ? 'active' : ''}`} onClick={() => changeMode('shop')}>
            <ShoppingBag size={18} /> Retail View
          </button>
          <button className={`mode-btn ${stats.mode === 'event' ? 'active' : ''}`} onClick={() => changeMode('event')}>
            <Activity size={18} /> Security View
          </button>
        </div>

        <div style={{ marginTop: 'auto' }}>
          <button
            className="mode-btn"
            style={{ width: '100%', justifyContent: 'center', background: isLive ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)', borderColor: isLive ? '#E74C3C' : '#2ECC71' }}
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Square size={16} /> : <Play size={16} />}
            {isLive ? "Stop Stream" : "Start Stream"}
          </button>
        </div>
      </aside>

      <main>
        {stats.alert && (
          <div className="alert-panel active">
            <AlertTriangle size={24} color="#E74C3C" />
            <div>
              <strong style={{ color: '#E74C3C' }}>CROWD WARNING!</strong>
              <p style={{ fontSize: '0.8rem', opacity: 0.8 }}>Density Threshold Exceeded. Monitor exits immediately.</p>
            </div>
          </div>
        )}

        <div className="metrics-grid">
          <div className="card">
            <div className="stat-label">{theme.mainLabel}</div>
            <div className="stat-value" style={{ color: theme.accent }}>{stats.count}</div>
            <div className="stat-label" style={{ fontSize: '0.6rem', marginTop: '4px' }}>{stats.availability}</div>
          </div>
          <div className="card">
            <div className="stat-label">Flow Level</div>
            <div className="stat-value">{stats.density}</div>
          </div>
          <div className="card">
            <div className="stat-label">Peak Pulse</div>
            <div className="stat-value">{stats.peak_count}</div>
          </div>
          <div className="card">
            <div className="stat-label">Engine FPS</div>
            <div className="stat-value" style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              {stats.fps} <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>FPS</span>
            </div>
          </div>
        </div>

        <div className="content-grid">
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="stat-label" style={{ padding: '1rem 1.5rem' }}>VISUAL ANALYSIS FEED</div>
            <div className="video-section">
              {isLive ? (
                <img
                  src={`${API_BASE}/video?t=${Date.now()}`}
                  alt="Live Feed"
                  style={{ filter: stats.mode === 'event' ? 'none' : 'contrast(1.1) brightness(0.9)' }}
                  onError={() => setStreamError(true)}
                />
              ) : (
                <div style={{ color: '#333' }}>IDLE</div>
              )}
            </div>
          </div>

          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="stat-label" style={{ marginBottom: '1rem' }}>{theme.subLabel}</div>
            {theme.gamifiedContent}

            <div className="ai-status">
              <div className="ai-tag">AI CORE V8.0</div>
              <p style={{ fontSize: '0.65rem', color: '#888' }}>Optimized Person-Detection Activated</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
