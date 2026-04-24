'use client';

import { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Wifi, WifiOff, RefreshCw, Zap, Grid, List } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Signal {
  signal: string;
  conviction: string;
  total_score: number;
  phase: string;
  primary_reason: string;
  institutional_narrative: string;
  entry: { price: number };
  stop_loss: { price: number };
  targets: { tp1?: number; tp2?: number };
  rr_ratio: number;
  fingerprints_detected: any;
  timestamp: string;
}

interface MarketState {
  price: number;
  delta: number;
  cumulative_delta: number;
  absorption: { detected: boolean; side?: string; duration_candles?: number };
  iceberg: { detected: boolean; refresh_count?: number };
  stop_hunt: { detected: boolean; direction?: string; confirmed?: boolean };
  divergence: string;
  spoofs_60s: number;
  top_bids: { price: number; qty: number }[];
  top_asks: { price: number; qty: number }[];
  phase: {
    absorption_active: boolean;
    stop_hunt_occurred: boolean;
    delta_confirmed: boolean;
    reclaim_confirmed: boolean;
  };
  latest_signal: Signal;
  timestamp: number;
}

export default function Dashboard() {
  const [marketState, setMarketState] = useState<MarketState | null>(null);
  const [signalHistory, setSignalHistory] = useState<Signal[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [deltaHistory, setDeltaHistory] = useState<{ time: string; delta: number; cumDelta: number }[]>([]);
  const [currentSymbol, setCurrentSymbol] = useState('BTCUSDT');
  const [availableSymbols, setAvailableSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'PAXGUSDT', 'XAUUSDT']);
  const [alertVisible, setAlertVisible] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertType, setAlertType] = useState<'LONG' | 'SHORT' | 'MONITOR' | null>(null);
  const [previousSignal, setPreviousSignal] = useState<string>('');
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      // Fetch market state
      const stateRes = await fetch(`${API_URL}/state`);
      if (!stateRes.ok) throw new Error('Failed to fetch state');
      const stateData = await stateRes.json();
      
      // Check for new signal
      const newSignal = stateData.latest_signal?.signal;
      const score = stateData.latest_signal?.total_score || 0;
      
      // Only alert if signal meets minimum threshold (score >= 6)
      if (newSignal && newSignal !== previousSignal && newSignal !== 'FLAT' && score >= 6) {
        // New qualifying signal detected!
        const conviction = stateData.latest_signal?.conviction || 'LOW';
        
        setAlertMessage(`${newSignal} Signal | ${conviction} Conviction | Score: ${score > 0 ? '+' : ''}${score}`);
        setAlertType(newSignal as 'LONG' | 'SHORT' | 'MONITOR');
        setAlertVisible(true);
        
        // Voice alert
        if (voiceEnabled && 'speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(
            `${newSignal} signal detected. ${conviction} conviction. Score: ${score}.`
          );
          utterance.rate = 1.1;
          utterance.pitch = 1;
          utterance.volume = 1;
          window.speechSynthesis.speak(utterance);
        }
        
        // Auto-hide alert after 8 seconds
        setTimeout(() => setAlertVisible(false), 8000);
      }
      
      // Update previous signal
      if (newSignal) {
        setPreviousSignal(newSignal);
      }
      
      setMarketState(stateData);
      setLastUpdate(new Date());
      setConnected(true);

      // Update delta history only if we have real data
      if (stateData.price > 0 || stateData.delta !== 0) {
        setDeltaHistory(prev => {
          const newPoint = {
            time: new Date().toLocaleTimeString(),
            delta: stateData.delta || 0,
            cumDelta: stateData.cumulative_delta || 0
          };
          const updated = [...prev, newPoint].slice(-50);
          return updated;
        });
      }

      // Fetch signal history
      const historyRes = await fetch(`${API_URL}/signals/history`);
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setSignalHistory(historyData.slice(0, 20));
      }

      // Fetch current symbol
      const symbolsRes = await fetch(`${API_URL}/symbols`);
      if (symbolsRes.ok) {
        const symbolsData = await symbolsRes.json();
        setCurrentSymbol(symbolsData.current);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSymbolChange = async (symbol: string) => {
    try {
      const res = await fetch(`${API_URL}/symbol/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol })
      });
      if (res.ok) {
        setCurrentSymbol(symbol);
        // Clear data while waiting for new symbol
        setDeltaHistory([]);
        setSignalHistory([]);
        setTimeout(fetchData, 2000); // Fetch after switch
      }
    } catch (error) {
      console.error('Failed to switch symbol:', error);
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'LONG': return 'text-green-400';
      case 'SHORT': return 'text-red-400';
      case 'MONITOR': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getConvictionColor = (conviction: string) => {
    switch (conviction) {
      case 'HIGH': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'LOW': return 'text-gray-400';
      default: return 'text-gray-500';
    }
  };

  const getPhaseBadge = (phase: string) => {
    const phases: Record<string, { color: string; label: string }> = {
      'NONE': { color: 'bg-gray-700', label: 'NO SIGNAL' },
      'ACCUMULATION': { color: 'bg-blue-900', label: 'ACCUMULATION' },
      'STOP_HUNT': { color: 'bg-orange-900', label: 'STOP HUNT' },
      'ENTRY_CONFIRMED': { color: 'bg-green-900', label: 'ENTRY CONFIRMED' },
      'MARKUP': { color: 'bg-emerald-900', label: 'MARKUP' }
    };
    const config = phases[phase] || phases['NONE'];
    return (
      <span className={`${config.color} px-3 py-1 rounded text-xs font-mono tracking-wider`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* Alert Banner */}
      {alertVisible && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-4 rounded-lg shadow-2xl border-2 animate-pulse ${
          alertType === 'LONG' ? 'bg-green-500/20 border-green-500 text-green-400' :
          alertType === 'SHORT' ? 'bg-red-500/20 border-red-500 text-red-400' :
          'bg-yellow-500/20 border-yellow-500 text-yellow-400'
        }`}>
          <div className="flex items-center gap-4">
            <div className="text-2xl">
              {alertType === 'LONG' ? '🟢' : alertType === 'SHORT' ? '🔴' : '🟡'}
            </div>
            <div>
              <div className="text-xl font-bold font-mono">{alertMessage}</div>
              <div className="text-xs mt-1">{currentSymbol} | {new Date().toLocaleTimeString()}</div>
            </div>
            <button 
              onClick={() => setAlertVisible(false)}
              className="ml-4 p-2 hover:bg-gray-800 rounded"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-mono tracking-wider">INSTITUTIONAL FOOTPRINT</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time Order Flow Detection System <span className="text-blue-400">| 5m Timeframe</span></p>
        </div>
        <div className="flex items-center gap-4">
          {/* View Toggle */}
          <div className="flex items-center gap-2 bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
            <a 
              href="/" 
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-mono transition"
              title="Single Symbol View"
            >
              <List className="w-4 h-4" />
              SINGLE
            </a>
            <a 
              href="/multi" 
              className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800 rounded text-sm font-mono transition text-gray-400 hover:text-white"
              title="Multi-Symbol View"
            >
              <Grid className="w-4 h-4" />
              MULTI
            </a>
          </div>
          {/* Symbol Selector */}
          <div className="flex items-center gap-2 bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
            <span className="text-xs text-gray-500">SYMBOL:</span>
            <select 
              value={currentSymbol}
              onChange={(e) => handleSymbolChange(e.target.value)}
              className="bg-transparent text-sm font-mono text-blue-400 focus:outline-none cursor-pointer"
            >
              {availableSymbols.map(sym => (
                <option key={sym} value={sym} className="bg-gray-900">{sym}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            {connected ? (
              <Wifi className="w-5 h-5 text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-400" />
            )}
            <span className={`text-sm ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Last update: {formatDistanceToNow(lastUpdate, { addSuffix: true })}
            </span>
          )}
          <button onClick={fetchData} className="p-2 hover:bg-gray-800 rounded transition" title="Refresh Data">
            <RefreshCw className="w-5 h-5" />
          </button>
          
          {/* Voice Alert Toggle */}
          <button 
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={`p-2 rounded transition ${voiceEnabled ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-800 hover:bg-gray-700'}`}
            title={voiceEnabled ? "Voice Alerts ON" : "Voice Alerts OFF"}
          >
            {voiceEnabled ? '🔊' : '🔇'}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">{currentSymbol} PRICE</div>
          <div className="text-2xl font-mono font-bold">
            ${marketState?.price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '—'}
          </div>
        </div>
        
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">DELTA</div>
          <div className={`text-2xl font-mono font-bold ${(marketState?.delta || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(marketState?.delta || 0) >= 0 ? '+' : ''}{marketState?.delta?.toFixed(2) || '—'}
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">CUMULATIVE DELTA</div>
          <div className={`text-2xl font-mono font-bold ${(marketState?.cumulative_delta || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(marketState?.cumulative_delta || 0) >= 0 ? '+' : ''}{marketState?.cumulative_delta?.toFixed(2) || '—'}
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500 mb-1">SPOOFS (60s)</div>
          <div className={`text-2xl font-mono font-bold ${(marketState?.spoofs_60s || 0) > 3 ? 'text-red-400' : (marketState?.spoofs_60s || 0) > 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
            {marketState?.spoofs_60s || 0}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Order Book & Delta Chart */}
        <div className="space-y-6">
          {/* Delta Chart */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-sm font-mono text-gray-400 mb-4">DELTA HISTORY</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={deltaHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#6B7280" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                  labelStyle={{ color: '#9CA3AF' }}
                />
                <Area type="monotone" dataKey="delta" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Order Book */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-sm font-mono text-gray-400 mb-4">ORDER BOOK</h3>
            <div className="space-y-1 font-mono text-xs">
              {marketState?.top_asks?.slice().reverse().map((ask, i) => (
                <div key={`ask-${i}`} className="flex justify-between items-center relative">
                  <div 
                    className="absolute right-0 top-0 bottom-0 bg-red-500/10 rounded"
                    style={{ width: `${Math.min((ask.qty / Math.max(...(marketState.top_asks || []).map(a => a.qty))) * 100, 100)}%` }}
                  />
                  <span className="text-gray-400 w-20 text-right relative z-10">{ask.qty.toFixed(3)}</span>
                  <span className="text-red-400 w-24 text-right relative z-10">${ask.price.toFixed(2)}</span>
                </div>
              ))}
              <div className="h-px bg-gray-700 my-2" />
              {marketState?.top_bids?.map((bid, i) => (
                <div key={`bid-${i}`} className="flex justify-between items-center relative">
                  <div 
                    className="absolute right-0 top-0 bottom-0 bg-green-500/10 rounded"
                    style={{ width: `${Math.min((bid.qty / Math.max(...(marketState.top_bids || []).map(b => b.qty))) * 100, 100)}%` }}
                  />
                  <span className="text-gray-400 w-20 text-right relative z-10">{bid.qty.toFixed(3)}</span>
                  <span className="text-green-400 w-24 text-right relative z-10">${bid.price.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Column - Current Signal */}
        <div className="space-y-6">
          {/* Phase Indicator */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-mono text-gray-400">MARKET PHASE</h3>
              {marketState && getPhaseBadge(marketState.latest_signal?.phase || 'NONE')}
            </div>
            <div className="grid grid-cols-4 gap-2">
              {['ACCUMULATION', 'STOP_HUNT', 'ENTRY_CONFIRMED', 'MARKUP'].map((phase, i) => {
                const currentPhase = marketState?.latest_signal?.phase || 'NONE';
                const phases = ['ACCUMULATION', 'STOP_HUNT', 'ENTRY_CONFIRMED', 'MARKUP'];
                const isActive = phases.indexOf(currentPhase) >= i;
                return (
                  <div key={phase} className="text-center">
                    <div className={`h-1 rounded mb-1 ${isActive ? 'bg-blue-500' : 'bg-gray-700'}`} />
                    <div className={`text-[8px] ${isActive ? 'text-gray-300' : 'text-gray-600'}`}>
                      {phase.replace('_', ' ')}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Latest Signal */}
          {marketState?.latest_signal && (
            <div className={`bg-gray-900 rounded-lg p-6 border-2 ${
              marketState.latest_signal.signal === 'LONG' ? 'border-green-500/30' :
              marketState.latest_signal.signal === 'SHORT' ? 'border-red-500/30' :
              'border-gray-700'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <div className={`text-3xl font-bold font-mono ${getSignalColor(marketState.latest_signal.signal)}`}>
                  {marketState.latest_signal.signal}
                </div>
                <div className="text-right">
                  <div className={`text-sm font-mono ${getConvictionColor(marketState.latest_signal.conviction)}`}>
                    {marketState.latest_signal.conviction}
                  </div>
                  <div className="text-xs text-gray-500">CONVICTION</div>
                </div>
              </div>

              {/* Score Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-500 mb-2">
                  <span>-12</span>
                  <span className={`font-mono font-bold ${
                    marketState.latest_signal.total_score >= 6 ? 'text-green-400' :
                    marketState.latest_signal.total_score <= -6 ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    SCORE: {marketState.latest_signal.total_score > 0 ? '+' : ''}{marketState.latest_signal.total_score}
                  </span>
                  <span>+12</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full relative">
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-600" />
                  <div 
                    className={`absolute h-full rounded-full transition-all ${
                      marketState.latest_signal.total_score >= 0 ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{
                      left: marketState.latest_signal.total_score >= 0 ? '50%' : `${50 + (marketState.latest_signal.total_score / 24 * 100)}%`,
                      width: `${Math.abs(marketState.latest_signal.total_score) / 24 * 100}%`
                    }}
                  />
                </div>
              </div>

              {/* Entry Details */}
              {marketState.latest_signal.entry?.price > 0 && (
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gray-800 rounded p-3 text-center">
                    <div className="text-[9px] text-gray-500 mb-1">ENTRY</div>
                    <div className="text-sm font-mono text-gray-300">
                      ${marketState.latest_signal.entry.price.toFixed(2)}
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded p-3 text-center">
                    <div className="text-[9px] text-gray-500 mb-1">STOP</div>
                    <div className="text-sm font-mono text-red-400">
                      ${marketState.latest_signal.stop_loss.price.toFixed(2)}
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded p-3 text-center">
                    <div className="text-[9px] text-gray-500 mb-1">TP2</div>
                    <div className="text-sm font-mono text-green-400">
                      ${marketState.latest_signal.targets?.tp2?.toFixed(2) || '—'}
                    </div>
                  </div>
                </div>
              )}

              {/* R:R Ratio */}
              {marketState.latest_signal.rr_ratio > 0 && (
                <div className="text-center mb-4">
                  <span className="text-xs text-gray-500">R:R </span>
                  <span className={`text-sm font-mono ${marketState.latest_signal.rr_ratio >= 2 ? 'text-green-400' : 'text-yellow-400'}`}>
                    1:{marketState.latest_signal.rr_ratio.toFixed(1)}
                  </span>
                </div>
              )}

              {/* Narrative */}
              {marketState.latest_signal.institutional_narrative && (
                <div className="bg-gray-800 rounded p-3 border-l-2 border-blue-500/30">
                  <div className="text-[9px] text-gray-500 mb-1">INSTITUTIONAL NARRATIVE</div>
                  <div className="text-xs text-gray-300 leading-relaxed">
                    {marketState.latest_signal.institutional_narrative}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Fingerprint Detection */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-sm font-mono text-gray-400 mb-4">FINGERPRINT DETECTION</h3>
            <div className="space-y-3">
              {[
                { name: 'ABSORPTION', detected: marketState?.absorption?.detected, detail: marketState?.absorption?.duration_candles ? `${marketState.absorption.side} | ${marketState.absorption.duration_candles} candles` : '' },
                { name: 'ICEBERG', detected: marketState?.iceberg?.detected, detail: marketState?.iceberg?.refresh_count ? `${marketState.iceberg.refresh_count} refreshes` : '' },
                { name: 'STOP HUNT', detected: marketState?.stop_hunt?.detected, detail: marketState?.stop_hunt?.direction || '' },
                { name: 'DELTA DIVERGENCE', detected: marketState?.divergence !== 'none', detail: marketState?.divergence !== 'none' ? marketState?.divergence : '' }
              ].map((fp, i) => (
                <div key={i} className="flex items-start gap-3 pb-3 border-b border-gray-800 last:border-0">
                  <div className={`w-2 h-2 rounded-full mt-1.5 ${fp.detected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-gray-700'}`} />
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className={`text-xs font-mono ${fp.detected ? 'text-gray-200' : 'text-gray-600'}`}>
                        {fp.name}
                      </span>
                      {fp.detected && <CheckCircle className="w-4 h-4 text-green-400" />}
                    </div>
                    {fp.detected && fp.detail && (
                      <div className="text-[10px] text-gray-500 mt-1">{fp.detail}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Signal History */}
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <h3 className="text-sm font-mono text-gray-400 mb-4">SIGNAL HISTORY</h3>
          <div className="space-y-3 max-h-[800px] overflow-y-auto">
            {signalHistory.length === 0 ? (
              <div className="text-center text-gray-600 text-sm py-8">
                Waiting for signals...
              </div>
            ) : (
              signalHistory.map((signal, i) => (
                <div 
                  key={i} 
                  className="bg-gray-800 rounded p-3 border-l-2 opacity-100 hover:opacity-80 transition"
                  style={{ 
                    borderColor: signal.signal === 'LONG' ? '#10B981' : signal.signal === 'SHORT' ? '#EF4444' : '#6B7280',
                    opacity: Math.max(0.4, 1 - i * 0.05)
                  }}
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className={`font-mono font-bold ${getSignalColor(signal.signal)}`}>
                      {signal.signal}
                    </span>
                    <span className={`text-xs ${getConvictionColor(signal.conviction)}`}>
                      {signal.conviction}
                    </span>
                  </div>
                  <div className="text-[10px] text-gray-500 mb-1">{signal.phase}</div>
                  {signal.total_score !== undefined && (
                    <div className="text-[10px] text-gray-400">
                      Score: {signal.total_score > 0 ? '+' : ''}{signal.total_score}
                    </div>
                  )}
                  {signal.primary_reason && (
                    <div className="text-[10px] text-gray-500 mt-2 line-clamp-2">
                      {signal.primary_reason}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
