import { useState, useEffect, useRef, useCallback } from "react";

// ─────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────
const WS_URL = "ws://localhost:8000/ws";
const API_URL = "http://localhost:8000";

// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────
const fmt = (n, d = 2) => n != null ? Number(n).toFixed(d) : "—";
const fmtK = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}K` : fmt(n, 2);

const PHASE_CONFIG = {
  NONE:           { label: "NO SIGNAL",       color: "#3a3a4a", glow: "none",                    pulse: false },
  ACCUMULATION:   { label: "ACCUMULATION",    color: "#1a3a5c", glow: "0 0 20px #1e6bb8",        pulse: true  },
  STOP_HUNT:      { label: "STOP HUNT",       color: "#4a2a0a", glow: "0 0 20px #e87c00",        pulse: true  },
  ENTRY_CONFIRMED:{ label: "ENTRY CONFIRMED", color: "#0a3a1a", glow: "0 0 30px #00e87c, 0 0 60px #00e87c44", pulse: true },
  MARKUP:         { label: "MARKUP",          color: "#0a2a1a", glow: "0 0 20px #00b85c",        pulse: false },
};

const SIGNAL_COLOR = { LONG: "#00e87c", SHORT: "#e83c3c", MONITOR: "#e8a800", FLAT: "#666" };
const CONVICTION_COLOR = { HIGH: "#00e87c", MEDIUM: "#e8a800", LOW: "#888", undefined: "#444" };

// ─────────────────────────────────────────────
// COMPONENTS
// ─────────────────────────────────────────────

function PhaseBadge({ phase }) {
  const cfg = PHASE_CONFIG[phase] || PHASE_CONFIG.NONE;
  return (
    <div style={{
      padding: "6px 16px",
      borderRadius: "4px",
      background: cfg.color,
      boxShadow: cfg.glow,
      fontSize: "11px",
      fontFamily: "'Share Tech Mono', monospace",
      letterSpacing: "2px",
      color: "#fff",
      animation: cfg.pulse ? "pulse 1.5s ease-in-out infinite" : "none",
      border: "1px solid rgba(255,255,255,0.1)"
    }}>
      {cfg.label}
    </div>
  );
}

function FingerprintRow({ label, detected, score, detail }) {
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: "12px",
      padding: "10px 0", borderBottom: "1px solid #1a1a2a"
    }}>
      <div style={{
        width: "8px", height: "8px", borderRadius: "50%", flexShrink: 0, marginTop: "4px",
        background: detected ? "#00e87c" : "#2a2a3a",
        boxShadow: detected ? "0 0 8px #00e87c" : "none"
      }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "11px", color: detected ? "#ccc" : "#555", letterSpacing: "1px", fontFamily: "'Share Tech Mono', monospace" }}>
            {label}
          </span>
          <span style={{
            fontSize: "13px", fontWeight: "bold",
            color: score > 0 ? "#00e87c" : score < 0 ? "#e83c3c" : "#555",
            fontFamily: "'Share Tech Mono', monospace"
          }}>
            {score > 0 ? `+${score}` : score}
          </span>
        </div>
        {detected && detail && (
          <div style={{ fontSize: "10px", color: "#666", marginTop: "3px", lineHeight: "1.4" }}>
            {detail}
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreBar({ score }) {
  const pct = ((score + 12) / 24) * 100;
  const color = score >= 6 ? "#00e87c" : score <= -6 ? "#e83c3c" : score >= 4 ? "#e8a800" : "#444";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
        <span style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>-12</span>
        <span style={{ fontSize: "13px", color, fontFamily: "'Share Tech Mono', monospace", fontWeight: "bold" }}>
          SCORE: {score > 0 ? `+${score}` : score} / 12
        </span>
        <span style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>+12</span>
      </div>
      <div style={{ height: "6px", background: "#1a1a2a", borderRadius: "3px", position: "relative" }}>
        <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: "1px", background: "#333" }} />
        <div style={{
          position: "absolute",
          left: score >= 0 ? "50%" : `${pct}%`,
          width: `${Math.abs(score) / 24 * 100}%`,
          height: "100%",
          background: color,
          boxShadow: `0 0 6px ${color}`,
          borderRadius: "3px",
          transition: "all 0.3s ease"
        }} />
      </div>
    </div>
  );
}

function OrderBookDOM({ bids = [], asks = [] }) {
  const maxQty = Math.max(...[...bids, ...asks].map(l => l.qty || 0), 1);
  return (
    <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: "11px" }}>
      {asks.slice().reverse().slice(0, 8).map((level, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "2px 0", position: "relative" }}>
          <div style={{
            position: "absolute", right: 0, top: 0, bottom: 0,
            width: `${(level.qty / maxQty) * 60}%`,
            background: "rgba(232, 60, 60, 0.12)", borderRadius: "2px"
          }} />
          <span style={{ color: "#888", width: "60px", textAlign: "right" }}>{fmt(level.qty, 3)}</span>
          <span style={{ color: "#e83c3c", width: "80px", textAlign: "right" }}>{fmt(level.price, 2)}</span>
        </div>
      ))}
      <div style={{ height: "1px", background: "#2a2a3a", margin: "4px 0" }} />
      {bids.slice(0, 8).map((level, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "2px 0", position: "relative" }}>
          <div style={{
            position: "absolute", right: 0, top: 0, bottom: 0,
            width: `${(level.qty / maxQty) * 60}%`,
            background: "rgba(0, 232, 124, 0.12)", borderRadius: "2px"
          }} />
          <span style={{ color: "#888", width: "60px", textAlign: "right" }}>{fmt(level.qty, 3)}</span>
          <span style={{ color: "#00e87c", width: "80px", textAlign: "right" }}>{fmt(level.price, 2)}</span>
        </div>
      ))}
    </div>
  );
}

function SignalCard({ signal }) {
  if (!signal || !signal.signal) return null;
  const col = SIGNAL_COLOR[signal.signal] || "#666";
  const conv = CONVICTION_COLOR[signal.conviction];

  return (
    <div style={{
      border: `1px solid ${col}44`,
      borderRadius: "8px",
      padding: "16px",
      background: `${col}08`,
      boxShadow: signal.signal !== "FLAT" ? `0 0 20px ${col}22` : "none"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <span style={{
          fontSize: "24px", fontWeight: "bold", color: col,
          fontFamily: "'Share Tech Mono', monospace",
          textShadow: signal.signal !== "FLAT" ? `0 0 10px ${col}` : "none"
        }}>
          {signal.signal}
        </span>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "11px", color: conv, fontFamily: "'Share Tech Mono', monospace" }}>
            {signal.conviction}
          </div>
          <div style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>
            CONVICTION
          </div>
        </div>
      </div>

      {signal.total_score != null && <ScoreBar score={signal.total_score} />}

      {signal.entry && signal.entry.price > 0 && (
        <div style={{ marginTop: "12px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
          {[
            ["ENTRY", signal.entry?.price, "#aaa"],
            ["STOP", signal.stop_loss?.price, "#e83c3c"],
            ["TP2", signal.targets?.tp2, "#00e87c"]
          ].map(([lbl, val, col]) => (
            <div key={lbl} style={{ background: "#0d0d1a", borderRadius: "4px", padding: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "9px", color: "#555", fontFamily: "'Share Tech Mono', monospace", marginBottom: "4px" }}>{lbl}</div>
              <div style={{ fontSize: "12px", color: col, fontFamily: "'Share Tech Mono', monospace" }}>{fmt(val, 2)}</div>
            </div>
          ))}
        </div>
      )}

      {signal.rr_ratio > 0 && (
        <div style={{ marginTop: "8px", textAlign: "center" }}>
          <span style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>R:R </span>
          <span style={{ fontSize: "13px", color: signal.rr_ratio >= 2 ? "#00e87c" : "#e8a800", fontFamily: "'Share Tech Mono', monospace" }}>
            1:{fmt(signal.rr_ratio, 1)}
          </span>
        </div>
      )}

      {signal.institutional_narrative && (
        <div style={{ marginTop: "12px", padding: "10px", background: "#0d0d1a", borderRadius: "4px", borderLeft: `2px solid ${col}44` }}>
          <div style={{ fontSize: "9px", color: "#555", fontFamily: "'Share Tech Mono', monospace", marginBottom: "4px" }}>INSTITUTIONAL NARRATIVE</div>
          <div style={{ fontSize: "11px", color: "#aaa", lineHeight: "1.5" }}>
            {signal.institutional_narrative}
          </div>
        </div>
      )}

      {signal.invalidation && (
        <div style={{ marginTop: "8px", fontSize: "10px", color: "#e83c3c88", fontFamily: "'Share Tech Mono', monospace" }}>
          ⚠ INVALIDATION: {signal.invalidation}
        </div>
      )}
    </div>
  );
}

function DeltaBar({ delta, cumDelta }) {
  const maxDelta = 500;
  const pct = Math.min(Math.abs(delta) / maxDelta * 50, 50);
  const col = delta >= 0 ? "#00e87c" : "#e83c3c";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <span style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>DELTA</span>
        <span style={{ fontSize: "12px", color: col, fontFamily: "'Share Tech Mono', monospace" }}>
          {delta >= 0 ? "+" : ""}{fmt(delta, 2)}
        </span>
      </div>
      <div style={{ height: "4px", background: "#1a1a2a", borderRadius: "2px", position: "relative" }}>
        <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: "1px", background: "#333" }} />
        <div style={{
          position: "absolute",
          left: delta >= 0 ? "50%" : `${50 - pct}%`,
          width: `${pct}%`,
          height: "100%",
          background: col,
          borderRadius: "2px",
          transition: "all 0.2s ease"
        }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px" }}>
        <span style={{ fontSize: "10px", color: "#555", fontFamily: "'Share Tech Mono', monospace" }}>CUM DELTA</span>
        <span style={{ fontSize: "12px", color: cumDelta >= 0 ? "#00e87c" : "#e83c3c", fontFamily: "'Share Tech Mono', monospace" }}>
          {cumDelta >= 0 ? "+" : ""}{fmt(cumDelta, 2)}
        </span>
      </div>
    </div>
  );
}

function AlertTicker({ signals }) {
  if (!signals.length) return null;
  const latest = signals[0];
  const col = SIGNAL_COLOR[latest.signal] || "#666";
  return (
    <div style={{
      padding: "8px 16px",
      background: `${col}15`,
      borderBottom: `1px solid ${col}33`,
      fontSize: "11px",
      fontFamily: "'Share Tech Mono', monospace",
      color: col,
      display: "flex",
      gap: "24px",
      alignItems: "center"
    }}>
      <span>◆ LAST SIGNAL</span>
      <span style={{ color: col }}>{latest.signal}</span>
      <span style={{ color: "#555" }}>|</span>
      <span>{latest.conviction}</span>
      <span style={{ color: "#555" }}>|</span>
      <span style={{ color: "#888" }}>{latest.primary_reason?.slice(0, 80)}...</span>
    </div>
  );
}

// ─────────────────────────────────────────────
// MAIN APP
// ─────────────────────────────────────────────

export default function App() {
  const [state, setState] = useState(null);
  const [signal, setSignal] = useState(null);
  const [signalHistory, setSignalHistory] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setLastUpdate(Date.now());

      if (msg.type === "market_update") {
        setState(msg.data);
        if (msg.data.latest_signal?.signal) {
          setSignal(msg.data.latest_signal);
        }
      } else if (msg.type === "signal") {
        setSignal(msg.data);
        setSignalHistory(prev => [msg.data, ...prev].slice(0, 50));
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectRef.current = setTimeout(connect, 3000);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const forceSignal = async () => {
    try {
      const res = await fetch(`${API_URL}/signal/force`, { method: "POST" });
      const data = await res.json();
      setSignal(data);
      setSignalHistory(prev => [data, ...prev].slice(0, 50));
    } catch (e) {
      console.error("Force signal failed:", e);
    }
  };

  const phase = state?.phase
    ? state.phase.entry_confirmed ? "ENTRY_CONFIRMED"
      : state.phase.stop_hunt_occurred ? "STOP_HUNT"
      : state.phase.absorption_active ? "ACCUMULATION"
      : "NONE"
    : "NONE";

  const fingerprints = signal?.fingerprints_detected || {};

  return (
    <div style={{
      minHeight: "100vh",
      background: "#07070f",
      color: "#ccc",
      fontFamily: "'Share Tech Mono', monospace"
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&display=swap');
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0d0d1a; }
        ::-webkit-scrollbar-thumb { background: #2a2a3a; border-radius: 2px; }
      `}</style>

      {/* HEADER */}
      <div style={{
        borderBottom: "1px solid #1a1a2a",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "#09090f"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: "22px", letterSpacing: "4px", color: "#fff" }}>
            INSTITUTIONAL ENTRY DETECTOR
          </div>
          <div style={{ fontSize: "11px", color: "#555", letterSpacing: "2px" }}>
            {state?.price ? `${state.symbol || "BTCUSDT"} @ ${fmt(state.price, 2)}` : "CONNECTING..."}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <PhaseBadge phase={phase} />
          <div style={{
            width: "8px", height: "8px", borderRadius: "50%",
            background: connected ? "#00e87c" : "#e83c3c",
            boxShadow: connected ? "0 0 8px #00e87c" : "0 0 8px #e83c3c",
            animation: connected ? "none" : "blink 1s infinite"
          }} />
          <button onClick={forceSignal} style={{
            background: "transparent",
            border: "1px solid #2a2a4a",
            color: "#888",
            padding: "6px 14px",
            borderRadius: "4px",
            fontSize: "10px",
            letterSpacing: "1px",
            cursor: "pointer",
            fontFamily: "'Share Tech Mono', monospace"
          }}>
            ▶ ANALYSE NOW
          </button>
        </div>
      </div>

      {/* ALERT TICKER */}
      {signalHistory.length > 0 && <AlertTicker signals={signalHistory} />}

      {/* MAIN GRID */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "300px 1fr 300px",
        gridTemplateRows: "auto 1fr",
        gap: "1px",
        background: "#1a1a2a",
        height: "calc(100vh - 56px - (signalHistory.length > 0 ? 36px : 0px))"
      }}>

        {/* LEFT — DOM + Delta */}
        <div style={{ background: "#09090f", padding: "16px", display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>
          <div>
            <div style={{ fontSize: "9px", color: "#555", letterSpacing: "2px", marginBottom: "12px" }}>ORDER BOOK</div>
            <OrderBookDOM bids={state?.top_bids || []} asks={state?.top_asks || []} />
          </div>

          <div style={{ borderTop: "1px solid #1a1a2a", paddingTop: "16px" }}>
            <div style={{ fontSize: "9px", color: "#555", letterSpacing: "2px", marginBottom: "12px" }}>DELTA</div>
            <DeltaBar delta={state?.delta || 0} cumDelta={state?.cumulative_delta || 0} />
          </div>

          <div style={{ borderTop: "1px solid #1a1a2a", paddingTop: "16px" }}>
            <div style={{ fontSize: "9px", color: "#555", letterSpacing: "2px", marginBottom: "12px" }}>SPOOF ACTIVITY</div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#888" }}>Last 60s</span>
              <span style={{
                fontSize: "14px",
                color: (state?.spoofs_60s || 0) > 3 ? "#e83c3c" : (state?.spoofs_60s || 0) > 0 ? "#e8a800" : "#555",
                fontWeight: "bold"
              }}>
                {state?.spoofs_60s || 0}
              </span>
            </div>
          </div>
        </div>

        {/* CENTER — Signal + Fingerprints */}
        <div style={{ background: "#09090f", padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "20px" }}>

          {/* Phase progress */}
          <div style={{ display: "flex", gap: "4px" }}>
            {["ACCUMULATION", "STOP_HUNT", "ENTRY_CONFIRMED", "MARKUP"].map((p, i) => {
              const phases = ["ACCUMULATION", "STOP_HUNT", "ENTRY_CONFIRMED", "MARKUP"];
              const currentIdx = phases.indexOf(phase);
              const active = i <= currentIdx;
              return (
                <div key={p} style={{ flex: 1 }}>
                  <div style={{
                    height: "3px",
                    background: active ? PHASE_CONFIG[p]?.glow.includes("#00e8") ? "#00e87c" : PHASE_CONFIG[p]?.glow.includes("#e87c") ? "#e87c00" : "#1e6bb8" : "#1a1a2a",
                    borderRadius: "2px",
                    marginBottom: "4px",
                    transition: "background 0.3s ease",
                    boxShadow: active ? "0 0 6px currentColor" : "none"
                  }} />
                  <div style={{ fontSize: "8px", color: active ? "#888" : "#333", letterSpacing: "1px", textAlign: "center" }}>
                    {p.replace("_", " ")}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Main signal */}
          <SignalCard signal={signal} />

          {/* Fingerprints */}
          <div>
            <div style={{ fontSize: "9px", color: "#555", letterSpacing: "2px", marginBottom: "4px" }}>FINGERPRINT DETECTION</div>
            <FingerprintRow
              label="ABSORPTION"
              detected={fingerprints.absorption?.detected || state?.absorption?.detected}
              score={fingerprints.absorption?.score || 0}
              detail={fingerprints.absorption?.detail || (state?.absorption?.detected ? `${state.absorption.side} absorption | ${state.absorption.duration_candles} candles` : "")}
            />
            <FingerprintRow
              label="ICEBERG ORDER"
              detected={fingerprints.iceberg?.detected || state?.iceberg?.detected}
              score={fingerprints.iceberg?.score || 0}
              detail={fingerprints.iceberg?.detail || (state?.iceberg?.detected ? `${state.iceberg.refresh_count} refreshes | est. ${fmtK(state.iceberg.estimated_true_size)} true size` : "")}
            />
            <FingerprintRow
              label="STOP HUNT"
              detected={fingerprints.stop_hunt?.detected || state?.stop_hunt?.detected}
              score={fingerprints.stop_hunt?.score || 0}
              detail={fingerprints.stop_hunt?.detail || (state?.stop_hunt?.detected ? `Swept ${fmt(state.stop_hunt.swept_level, 2)} | ${state.stop_hunt.volume_spike_ratio}x volume | Reclaimed: ${state.stop_hunt.price_reclaimed}` : "")}
            />
            <FingerprintRow
              label="DELTA DIVERGENCE"
              detected={fingerprints.delta_divergence?.detected || state?.divergence !== "none"}
              score={fingerprints.delta_divergence?.score || 0}
              detail={fingerprints.delta_divergence?.detail || (state?.divergence !== "none" ? `${state?.divergence} divergence detected` : "")}
            />
            <FingerprintRow
              label="VOLUME SPIKE"
              detected={fingerprints.volume_spike?.detected}
              score={fingerprints.volume_spike?.score || 0}
              detail={fingerprints.volume_spike?.detail || ""}
            />
          </div>

          {/* Conflicts / Warnings */}
          {signal?.conflicts?.length > 0 && (
            <div style={{ padding: "12px", background: "#1a0a0a", borderRadius: "6px", border: "1px solid #e83c3c22" }}>
              <div style={{ fontSize: "9px", color: "#e83c3c88", letterSpacing: "2px", marginBottom: "8px" }}>CONFLICTS</div>
              {signal.conflicts.map((c, i) => (
                <div key={i} style={{ fontSize: "11px", color: "#e83c3c88", marginBottom: "4px" }}>◆ {c}</div>
              ))}
            </div>
          )}

          {signal?.warnings?.length > 0 && (
            <div style={{ padding: "12px", background: "#1a1200", borderRadius: "6px", border: "1px solid #e8a80022" }}>
              <div style={{ fontSize: "9px", color: "#e8a80088", letterSpacing: "2px", marginBottom: "8px" }}>WARNINGS</div>
              {signal.warnings.map((w, i) => (
                <div key={i} style={{ fontSize: "11px", color: "#e8a80088", marginBottom: "4px" }}>⚠ {w}</div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT — Signal History */}
        <div style={{ background: "#09090f", padding: "16px", overflowY: "auto" }}>
          <div style={{ fontSize: "9px", color: "#555", letterSpacing: "2px", marginBottom: "12px" }}>SIGNAL HISTORY</div>
          {signalHistory.length === 0 ? (
            <div style={{ fontSize: "11px", color: "#333", textAlign: "center", marginTop: "40px" }}>
              Waiting for signals...
            </div>
          ) : (
            signalHistory.map((s, i) => {
              const col = SIGNAL_COLOR[s.signal] || "#666";
              return (
                <div key={i} style={{
                  padding: "10px",
                  marginBottom: "8px",
                  background: "#0d0d1a",
                  borderRadius: "4px",
                  borderLeft: `2px solid ${col}66`,
                  opacity: i === 0 ? 1 : Math.max(0.4, 1 - i * 0.07)
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ fontSize: "13px", color: col, fontWeight: "bold" }}>{s.signal}</span>
                    <span style={{ fontSize: "10px", color: CONVICTION_COLOR[s.conviction] }}>{s.conviction}</span>
                  </div>
                  <div style={{ fontSize: "10px", color: "#555" }}>{s.phase}</div>
                  {s.total_score != null && (
                    <div style={{ fontSize: "10px", color: "#444", marginTop: "4px" }}>
                      Score: {s.total_score > 0 ? "+" : ""}{s.total_score}
                    </div>
                  )}
                  {s.primary_reason && (
                    <div style={{ fontSize: "10px", color: "#555", marginTop: "4px", lineHeight: "1.4" }}>
                      {s.primary_reason?.slice(0, 80)}...
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
