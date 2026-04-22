import React, { useState, useEffect } from 'react';

const XAUUSDSMCDashboard = () => {
  const [smcData, setSmcData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSMCData = async () => {
    try {
      const response = await fetch('/api/xauusd-smc');
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

  const getBiasColor = (bias) => {
    switch (bias) {
      case 'bullish': return 'text-green-500 bg-green-100';
      case 'bearish': return 'text-red-500 bg-red-100';
      default: return 'text-gray-500 bg-gray-100';
    }
  };

  const getSignalColor = (direction) => {
    return direction === 'bullish' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50';
  };

  const formatPrice = (price) => {
    return `$${parseFloat(price).toFixed(2)}`;
  };

  const formatConfidence = (confidence) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading XAUUSD SMC Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            XAUUSD Smart Money Concepts Monitor
          </h1>
          <p className="text-gray-600">
            Real-time BOS/CHOCH • FVG • Liquidity Zones • HTF Bias Analysis
          </p>
          {lastUpdate && (
            <p className="text-sm text-gray-500 mt-2">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>

        {error && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-6">
            <p className="text-yellow-700">{error}</p>
          </div>
        )}

        {smcData && (
          <>
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Current Price */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Current Price</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {formatPrice(smcData.current_price)}
                </p>
              </div>

              {/* ATR */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">ATR (14)</h3>
                <p className="text-3xl font-bold text-blue-600">
                  {formatPrice(smcData.atr)}
                </p>
              </div>

              {/* HTF Bias */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">HTF Bias (4H)</h3>
                <span className={`inline-block px-4 py-2 rounded-full text-lg font-semibold ${getBiasColor(smcData.htf_bias)}`}>
                  {smcData.htf_bias.toUpperCase()}
                </span>
              </div>

              {/* Active Structures */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Active Signals</h3>
                <p className="text-3xl font-bold text-purple-600">
                  {smcData.signals?.length || 0}
                </p>
              </div>
            </div>

            {/* Market Structure & Confluence */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Active FVGs */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Fair Value Gaps</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Active FVGs:</span>
                    <span className="text-2xl font-bold text-indigo-600">{smcData.active_fvgs}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Bullish FVGs act as support zones</p>
                    <p>Bearish FVGs act as resistance zones</p>
                  </div>
                </div>
              </div>

              {/* Liquidity Zones */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Liquidity Zones</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Total Zones:</span>
                    <span className="text-2xl font-bold text-orange-600">{smcData.liquidity_zones}</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Buyside: Target for bullish moves</p>
                    <p>Sellside: Target for bearish moves</p>
                  </div>
                </div>
              </div>

              {/* Recent Structures */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Structure</h3>
                <div className="space-y-2">
                  {smcData.structures && smcData.structures.length > 0 ? (
                    smcData.structures.map((struct, idx) => (
                      <div key={idx} className={`p-3 rounded-lg border-l-4 ${
                        struct.direction === 'bullish' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
                      }`}>
                        <p className="font-semibold">{struct.type}</p>
                        <p className="text-sm text-gray-600 capitalize">{struct.direction}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-sm">No recent structure breaks</p>
                  )}
                </div>
              </div>
            </div>

            {/* Trading Signals */}
            {smcData.signals && smcData.signals.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  🚨 Active Trading Signals ({smcData.signals.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {smcData.signals.map((signal, idx) => (
                    <div 
                      key={idx} 
                      className={`border-l-4 p-4 rounded-lg ${getSignalColor(signal.direction)}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-lg">
                          {signal.type} - {signal.direction.toUpperCase()}
                        </h4>
                        <span className="text-sm font-semibold text-gray-600">
                          {formatPrice(signal.price)}
                        </span>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Confidence:</span>
                          <span className="font-semibold">{formatConfidence(signal.confidence)}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-600">HTF Bias:</span>
                          <span className={`font-semibold ${getBiasColor(signal.htf_bias)}`}>
                            {signal.htf_bias.toUpperCase()}
                          </span>
                        </div>
                        
                        <p className="text-gray-700 mt-2">{signal.description}</p>
                        
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(signal.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Strategy Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">Strategy Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
                <div>
                  <h4 className="font-semibold mb-2">Smart Money Concepts:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>BOS:</strong> Break of Structure (trend continuation)</li>
                    <li><strong>CHOCH:</strong> Change of Character (trend reversal)</li>
                    <li><strong>FVG:</strong> Fair Value Gaps (imbalances)</li>
                    <li><strong>Liquidity:</strong> Buyside/Sellside zones</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Signal Generation:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Structure break detection</li>
                    <li>HTF bias alignment (+20% confidence)</li>
                    <li>FVG confluence (+15% confidence)</li>
                    <li>Liquidity zone proximity (+15% confidence)</li>
                    <li>Minimum 60% confidence threshold</li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default XAUUSDSMCDashboard;
