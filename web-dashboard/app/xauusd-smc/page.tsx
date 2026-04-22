'use client';

import React, { useState, useEffect } from 'react';

interface SMCData {
  timestamp: string;
  current_price: number;
  atr: number;
  htf_bias: string;
  structures: Array<{ type: string; direction: string }>;
  active_fvgs: number;
  liquidity_zones: number;
  signals: Array<{
    type: string;
    direction: string;
    price: number;
    confidence: number;
    description: string;
    timestamp: string;
    htf_bias: string;
  }>;
}

export default function XAUUSDSMCDashboard() {
  const [smcData, setSmcData] = useState<SMCData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchSMCData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/xauusd-smc');
      const result = await response.json();
      
      if (result.status === 'success') {
        setSmcData(result.data);
        setLastUpdate(new Date());
        setError(null);
      } else if (result.status === 'pending') {
        setError('Monitor is starting up. Please wait...');
      } else {
        setError(result.message || 'Failed to fetch data');
      }
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSMCData();
    const interval = setInterval(fetchSMCData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'bullish': return 'text-green-600 bg-green-100 border-green-300';
      case 'bearish': return 'text-red-600 bg-red-100 border-red-300';
      default: return 'text-gray-600 bg-gray-100 border-gray-300';
    }
  };

  const getSignalColor = (direction: string) => {
    return direction === 'bullish' 
      ? 'border-l-4 border-green-500 bg-gradient-to-r from-green-50 to-white' 
      : 'border-l-4 border-red-500 bg-gradient-to-r from-red-50 to-white';
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div className="text-xl text-white font-semibold">Loading XAUUSD SMC Dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold text-white mb-2 tracking-tight">
            XAUUSD Smart Money Concepts
          </h1>
          <p className="text-slate-400 text-lg">
            Real-time BOS/CHOCH • FVG • Liquidity Zones • HTF Bias Analysis
          </p>
          {lastUpdate && (
            <p className="text-sm text-slate-500 mt-2">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>

        {error && (
          <div className="bg-yellow-900/30 border-l-4 border-yellow-500 p-4 mb-6 rounded-lg backdrop-blur-sm">
            <p className="text-yellow-200">{error}</p>
          </div>
        )}

        {smcData && (
          <>
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Current Price */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700 hover:border-blue-500 transition-all">
                <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wider">Current Price</h3>
                <p className="text-4xl font-bold text-white">
                  {formatPrice(smcData.current_price)}
                </p>
              </div>

              {/* ATR */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700 hover:border-blue-500 transition-all">
                <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wider">ATR (14)</h3>
                <p className="text-4xl font-bold text-blue-400">
                  {formatPrice(smcData.atr)}
                </p>
              </div>

              {/* HTF Bias */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700 hover:border-blue-500 transition-all">
                <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wider">HTF Bias (4H)</h3>
                <span className={`inline-block px-6 py-3 rounded-lg text-xl font-bold border ${getBiasColor(smcData.htf_bias)}`}>
                  {smcData.htf_bias.toUpperCase()}
                </span>
              </div>

              {/* Active Signals */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700 hover:border-blue-500 transition-all">
                <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wider">Active Signals</h3>
                <p className="text-4xl font-bold text-purple-400">
                  {smcData.signals?.length || 0}
                </p>
              </div>
            </div>

            {/* Market Structure & Confluence */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Active FVGs */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                  <span className="mr-2">📊</span> Fair Value Gaps
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-300">Active FVGs:</span>
                    <span className="text-3xl font-bold text-indigo-400">{smcData.active_fvgs}</span>
                  </div>
                  <div className="text-sm text-slate-400 space-y-1">
                    <p>• Bullish FVGs act as support zones</p>
                    <p>• Bearish FVGs act as resistance zones</p>
                  </div>
                </div>
              </div>

              {/* Liquidity Zones */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                  <span className="mr-2">💧</span> Liquidity Zones
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-300">Total Zones:</span>
                    <span className="text-3xl font-bold text-orange-400">{smcData.liquidity_zones}</span>
                  </div>
                  <div className="text-sm text-slate-400 space-y-1">
                    <p>• Buyside: Target for bullish moves</p>
                    <p>• Sellside: Target for bearish moves</p>
                  </div>
                </div>
              </div>

              {/* Recent Structures */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 border border-slate-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                  <span className="mr-2">🏗️</span> Market Structure
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {smcData.structures && smcData.structures.length > 0 ? (
                    smcData.structures.map((struct, idx) => (
                      <div key={idx} className={`p-3 rounded-lg border-l-4 ${
                        struct.direction === 'bullish' 
                          ? 'border-green-500 bg-green-900/20' 
                          : 'border-red-500 bg-red-900/20'
                      }`}>
                        <p className="font-semibold text-white">{struct.type}</p>
                        <p className="text-sm text-slate-400 capitalize">{struct.direction}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm italic">No recent structure breaks</p>
                  )}
                </div>
              </div>
            </div>

            {/* Trading Signals */}
            {smcData.signals && smcData.signals.length > 0 && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl shadow-xl p-6 mb-8 border border-slate-700">
                <h3 className="text-2xl font-semibold text-white mb-4 flex items-center">
                  <span className="mr-2">🚨</span> Active Trading Signals ({smcData.signals.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {smcData.signals.map((signal, idx) => (
                    <div 
                      key={idx} 
                      className={`${getSignalColor(signal.direction)} p-5 rounded-lg shadow-md hover:shadow-lg transition-shadow`}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h4 className="font-bold text-xl text-slate-900">
                          {signal.type} - {signal.direction.toUpperCase()}
                        </h4>
                        <span className="text-lg font-bold text-slate-700">
                          {formatPrice(signal.price)}
                        </span>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600 font-medium">Confidence:</span>
                          <span className="font-bold text-slate-900">{formatConfidence(signal.confidence)}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-slate-600 font-medium">HTF Bias:</span>
                          <span className={`font-bold px-2 py-1 rounded ${getBiasColor(signal.htf_bias)}`}>
                            {signal.htf_bias.toUpperCase()}
                          </span>
                        </div>
                        
                        <p className="text-slate-700 mt-3 font-medium">{signal.description}</p>
                        
                        <p className="text-xs text-slate-500 mt-3">
                          {new Date(signal.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Strategy Info */}
            <div className="bg-blue-900/20 border border-blue-700/50 rounded-xl p-6 backdrop-blur-sm">
              <h3 className="text-xl font-semibold text-blue-300 mb-3 flex items-center">
                <span className="mr-2">📚</span> Strategy Overview
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-blue-200">
                <div>
                  <h4 className="font-semibold mb-2 text-blue-100">Smart Money Concepts:</h4>
                  <ul className="space-y-1">
                    <li><strong className="text-white">BOS:</strong> Break of Structure (trend continuation)</li>
                    <li><strong className="text-white">CHOCH:</strong> Change of Character (trend reversal)</li>
                    <li><strong className="text-white">FVG:</strong> Fair Value Gaps (imbalances)</li>
                    <li><strong className="text-white">Liquidity:</strong> Buyside/Sellside zones</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2 text-blue-100">Signal Generation:</h4>
                  <ul className="space-y-1">
                    <li>• Structure break detection</li>
                    <li>• HTF bias alignment (+20% confidence)</li>
                    <li>• FVG confluence (+15% confidence)</li>
                    <li>• Liquidity zone proximity (+15% confidence)</li>
                    <li>• Minimum 60% confidence threshold</li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
