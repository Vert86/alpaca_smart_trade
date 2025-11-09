import React, { useState } from 'react';
import './TradingPanel.css';

function TradingPanel({ results, onExecuteTrade, onRefresh }) {
  const [selectedStock, setSelectedStock] = useState(null);
  const [orderType, setOrderType] = useState('market');
  const [limitPrice, setLimitPrice] = useState('');
  const [customQuantity, setCustomQuantity] = useState('');
  const [executing, setExecuting] = useState(false);
  const [tradeResult, setTradeResult] = useState(null);

  if (!results || !results.analysis) {
    return null;
  }

  const { buy_recommendations, sell_recommendations } = results.analysis;
  const tradableRecommendations = [...buy_recommendations, ...sell_recommendations];

  const handleExecute = async () => {
    if (!selectedStock) return;

    setExecuting(true);
    setTradeResult(null);

    const quantity = customQuantity || selectedStock.position_size;

    const tradeDetails = {
      symbol: selectedStock.symbol,
      action: selectedStock.action,
      quantity: parseInt(quantity),
      order_type: orderType,
      ...(orderType === 'limit' && { limit_price: parseFloat(limitPrice) })
    };

    const result = await onExecuteTrade(tradeDetails);

    setTradeResult(result);
    setExecuting(false);

    if (result.success) {
      setTimeout(() => {
        setSelectedStock(null);
        setTradeResult(null);
        onRefresh();
      }, 3000);
    }
  };

  return (
    <div className="trading-panel">
      <h3>⚡ Trade Execution</h3>

      {tradableRecommendations.length === 0 ? (
        <div className="no-trades">
          <p>No tradable recommendations at this time</p>
        </div>
      ) : (
        <>
          <div className="trade-selector">
            <label>Select Stock to Trade:</label>
            <select
              value={selectedStock?.symbol || ''}
              onChange={(e) => {
                const stock = tradableRecommendations.find(r => r.symbol === e.target.value);
                setSelectedStock(stock);
                setCustomQuantity('');
                setLimitPrice('');
                setTradeResult(null);
              }}
            >
              <option value="">-- Select a stock --</option>
              {tradableRecommendations.map(rec => (
                <option key={rec.symbol} value={rec.symbol}>
                  {rec.symbol} - {rec.action} ({(rec.confidence * 100).toFixed(0)}% confidence)
                </option>
              ))}
            </select>
          </div>

          {selectedStock && (
            <div className="trade-details">
              <div className="trade-info">
                <h4>{selectedStock.symbol}</h4>
                <div className="info-row">
                  <span>Action:</span>
                  <span className={`action-badge ${selectedStock.action.toLowerCase()}`}>
                    {selectedStock.action}
                  </span>
                </div>
                <div className="info-row">
                  <span>Suggested Quantity:</span>
                  <span>{selectedStock.position_size} shares</span>
                </div>
                {selectedStock.position_value > 0 && (
                  <div className="info-row">
                    <span>Estimated Value:</span>
                    <span>${selectedStock.position_value.toLocaleString()}</span>
                  </div>
                )}
                <div className="info-row">
                  <span>Confidence:</span>
                  <span>{(selectedStock.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="trade-options">
                <div className="form-group">
                  <label>Order Type:</label>
                  <div className="radio-group">
                    <label>
                      <input
                        type="radio"
                        value="market"
                        checked={orderType === 'market'}
                        onChange={(e) => setOrderType(e.target.value)}
                      />
                      Market Order
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="limit"
                        checked={orderType === 'limit'}
                        onChange={(e) => setOrderType(e.target.value)}
                      />
                      Limit Order
                    </label>
                  </div>
                </div>

                {orderType === 'limit' && (
                  <div className="form-group">
                    <label>Limit Price:</label>
                    <input
                      type="number"
                      step="0.01"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(e.target.value)}
                      placeholder="Enter limit price"
                    />
                  </div>
                )}

                <div className="form-group">
                  <label>Quantity (optional):</label>
                  <input
                    type="number"
                    value={customQuantity}
                    onChange={(e) => setCustomQuantity(e.target.value)}
                    placeholder={`Default: ${selectedStock.position_size}`}
                  />
                </div>
              </div>

              {tradeResult && (
                <div className={`trade-result ${tradeResult.success ? 'success' : 'error'}`}>
                  {tradeResult.success ? (
                    <>
                      <span className="result-icon">✅</span>
                      <div>
                        <strong>Trade Executed Successfully!</strong>
                        <p>Order ID: {tradeResult.order?.id}</p>
                        <p>Status: {tradeResult.order?.status}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <span className="result-icon">❌</span>
                      <div>
                        <strong>Trade Failed</strong>
                        <p>{tradeResult.error}</p>
                      </div>
                    </>
                  )}
                </div>
              )}

              <div className="trade-actions">
                <button
                  className="btn btn-execute"
                  onClick={handleExecute}
                  disabled={executing || (orderType === 'limit' && !limitPrice)}
                >
                  {executing ? 'Executing...' : `Execute ${selectedStock.action}`}
                </button>
                <button
                  className="btn btn-cancel"
                  onClick={() => {
                    setSelectedStock(null);
                    setTradeResult(null);
                  }}
                  disabled={executing}
                >
                  Cancel
                </button>
              </div>

              <div className="trade-warning">
                ⚠️ Warning: This will execute a real trade on your Alpaca account.
                Please review carefully before confirming.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default TradingPanel;
