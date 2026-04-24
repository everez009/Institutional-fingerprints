'use client';

import { useState, useEffect, useCallback } from 'react';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Wifi, WifiOff, RefreshCw, Grid, List } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SymbolData {
  symbol: string;
  price: number;
  delta: number;
  cumulative_delta: number;
  signal: string;
  conviction: string;
  score: number;
  phase: string;
  absorption: boolean;
  iceberg: boolean;
  stop_hunt: boolean;
  divergence: string;
  spoofs_60s: number;
  timestamp: number;
}

export default function MultiSymbolDashboard() {
  const [symbols, setSymbols] = useState<SymbolData[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [availableSymbols, setAvailableSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'PAXGUSDT']);
  const [alerts, setAlerts] = useState<Array<{symbol: string, message: string, type: string, time: Date}>>([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [previousSignals, setPreviousSignals] = useState<Record<string, string>>({});

  const fetchData = useCallback(async () => {
    try {
      // Fetch multi-symbol summary
      const summaryRes = await fetch(`${API_URL}/multi/summary`);
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        
        // Check for new signals
        summaryData.forEach((sym: SymbolData) => {
          const currentSignal = sym.signal;
          const prevSignal = previousSignals[sym.symbol];
          
          if (currentSignal && currentSignal !== prevSignal && currentSignal !== 'FLAT') {
            // New signal detected!
            const message = `${sym.symbol}: ${currentSignal} | ${sym.conviction} | Score: ${sym.score > 0 ? '+' : ''}${sym.score}`;
            
            // Add to alerts
            setAlerts(prev => [{
              symbol: sym.symbol,
              message,
              type: currentSignal,
              time: new Date()
            }, ...prev].slice(0, 5)); // Keep last 5 alerts
            
            // Voice alert for HIGH or MEDIUM conviction
            if (voiceEnabled && (sym.conviction === 'HIGH' || sym.conviction === 'MEDIUM') && 'speechSynthesis' in window) {
              const utterance = new SpeechSynthesisUtterance(
                `${sym.symbol} ${currentSignal} signal. ${sym.conviction} conviction.`
              );
              utterance.rate = 1.1;
              window.speechSynthesis.speak(utterance);
            }
            
            // Update previous signal
            setPreviousSignals(prev => ({ ...prev, [sym.symbol]: currentSignal }));
          }
        });
        
        setSymbols(summaryData);
        setLastUpdate(new Date());
        setConnected(true);
      }

      // Fetch available symbols
      const symbolsRes = await fetch(`${API_URL}/symbols`);
      if (symbolsRes.ok) {
        const symbolsData = await symbolsRes.json();
        setAvailableSymbols(symbolsData.supported);
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

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'LONG': return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'SHORT': return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'MONITOR': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      default: return 'text-gray-400 bg-gray-500/10 border-gray-700';
    }
  };

  const getConvictionBadge = (conviction: string, score: number) => {
    const colors = {
      HIGH: 'bg-green-500/20 text-green-400',
      MEDIUM: 'bg-yellow-500/20 text-yellow-400',
      LOW: 'bg-gray-500/20 text-gray-400'
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-mono ${colors[conviction as keyof typeof colors]}`}>
        {conviction} ({score > 0 ? '+' : ''}{score})
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* Alert Banner */}
      {alerts.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
          {alerts.map((alert, i) => (
            <div 
              key={i}
              className={`px-4 py-3 rounded-lg shadow-xl border-2 animate-pulse ${
                alert.type === 'LONG' ? 'bg-green-500/20 border-green-500 text-green-400' :
                alert.type === 'SHORT' ? 'bg-red-500/20 border-red-500 text-red-400' :
                'bg-yellow-500/20 border-yellow-500 text-yellow-400'
              }`}
              style={{ animationDuration: '2s' }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-bold font-mono">{alert.message}</div>
                  <div className="text-xs mt-1">{alert.time.toLocaleTimeString()}</div>
                </div>
                <button 
                  onClick={() => setAlerts(prev => prev.filter((_, idx) => idx !== i))}
                  className="ml-2 p-1 hover:bg-gray-800 rounded"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-mono tracking-wider">INSTITUTIONAL FOOTPRINT</h1>
          <p className="text-sm text-gray-500 mt-1">Multi-Symbol Real-Time Monitoring <span className="text-blue-400">| 5m Timeframe</span></p>
        </div>
        <div className="flex items-center gap-4">
          {/* View Toggle */}
          <div className="flex items-center gap-2 bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
            <a 
              href="/" 
              className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800 rounded text-sm font-mono transition text-gray-400 hover:text-white"
              title="Single Symbol View"
            >
              <List className="w-4 h-4" />
              SINGLE
            </a>
            <a 
              href="/multi" 
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-mono transition"
              title="Multi-Symbol View"
            >
              <Grid className="w-4 h-4" />
              MULTI
            </a>
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

      {/* Symbols Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {symbols.map((sym) => (
          <div key={sym.symbol} className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
            {/* Symbol Header */}
            <div className="bg-gray-800/50 px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <h2 className="text-xl font-bold font-mono">{sym.symbol}</h2>
              <div className={`text-2xl font-mono font-bold ${sym.price > 0 ? 'text-white' : 'text-gray-600'}`}>
                ${sym.price > 0 ? sym.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}
              </div>
            </div>

            {/* Signal Card */}
            <div className={`m-4 p-4 rounded-lg border-2 ${getSignalColor(sym.signal)}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl font-bold font-mono">{sym.signal}</span>
                {getConvictionBadge(sym.conviction, sym.score)}
              </div>
              <div className="text-xs text-gray-400 font-mono">{sym.phase}</div>
            </div>

            {/* Metrics */}
            <div className="px-4 pb-4 space-y-3">
              {/* Delta */}
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">DELTA</span>
                <span className={`font-mono font-bold ${sym.delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {sym.delta >= 0 ? '+' : ''}{sym.delta.toFixed(2)}
                </span>
              </div>

              {/* Cumulative Delta */}
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">CUM DELTA</span>
                <span className={`font-mono ${(sym.cumulative_delta || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(sym.cumulative_delta || 0) >= 0 ? '+' : ''}{(sym.cumulative_delta || 0).toFixed(2)}
                </span>
              </div>

              {/* Spoofs */}
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">SPOOFS (60s)</span>
                <span className={`font-mono font-bold ${(sym.spoofs_60s || 0) > 3 ? 'text-red-400' : (sym.spoofs_60s || 0) > 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
                  {sym.spoofs_60s || 0}
                </span>
              </div>

              {/* Fingerprints */}
              <div className="pt-3 border-t border-gray-800">
                <div className="text-xs text-gray-500 mb-2">FINGERPRINTS</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${sym.absorption ? 'bg-green-400' : 'bg-gray-700'}`} />
                    <span className="text-[10px] text-gray-400">ABSORPTION</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${sym.iceberg ? 'bg-green-400' : 'bg-gray-700'}`} />
                    <span className="text-[10px] text-gray-400">ICEBERG</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${sym.stop_hunt ? 'bg-green-400' : 'bg-gray-700'}`} />
                    <span className="text-[10px] text-gray-400">STOP HUNT</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${sym.divergence !== 'none' ? 'bg-green-400' : 'bg-gray-700'}`} />
                    <span className="text-[10px] text-gray-400">DIVERGENCE</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {symbols.length === 0 && connected && (
        <div className="text-center py-20">
          <Activity className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">Waiting for market data...</p>
        </div>
      )}

      {!connected && (
        <div className="text-center py-20">
          <WifiOff className="w-16 h-16 text-red-500/50 mx-auto mb-4" />
          <p className="text-red-400">Disconnected from server</p>
        </div>
      )}
    </div>
  );
}
