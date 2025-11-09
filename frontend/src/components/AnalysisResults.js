import React, { useState } from 'react';
import './AnalysisResults.css';

function AnalysisResults({ results }) {
  const [selectedTab, setSelectedTab] = useState('recommendations');
  const [expandedStock, setExpandedStock] = useState(null);

  if (!results || !results.analysis) {
    return null;
  }

  const { analysis, detailed_results } = results;
  const { buy_recommendations, sell_recommendations, hold_recommendations, summary } = analysis;

  const getActionColor = (action) => {
    switch (action) {
      case 'BUY': return '#10b981';
      case 'SELL': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'BUY': return '🟢';
      case 'SELL': return '🔴';
      default: return '🟡';
    }
  };

  const renderRecommendationCard = (rec) => {
    const isExpanded = expandedStock === rec.symbol;

    return (
      <div key={rec.symbol} className="recommendation-card">
        <div
          className="rec-header"
          onClick={() => setExpandedStock(isExpanded ? null : rec.symbol)}
          style={{ cursor: 'pointer' }}
        >
          <div className="rec-title">
            <span className="rec-icon">{getActionIcon(rec.action)}</span>
            <span className="rec-symbol">{rec.symbol}</span>
            <span className="rec-action" style={{ color: getActionColor(rec.action) }}>
              {rec.action}
            </span>
          </div>
          <div className="rec-confidence">
            <div className="confidence-bar-container">
              <div
                className="confidence-bar"
                style={{
                  width: `${rec.confidence * 100}%`,
                  backgroundColor: getActionColor(rec.action)
                }}
              />
            </div>
            <span className="confidence-text">{(rec.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>

        {isExpanded && (
          <div className="rec-details">
            <div className="detail-section">
              <h4>Position Details</h4>
              {rec.action === 'BUY' && (
                <>
                  <p><strong>Suggested Quantity:</strong> {rec.position_size} shares</p>
                  <p><strong>Estimated Value:</strong> ${rec.position_value.toLocaleString()}</p>
                </>
              )}
              {rec.action === 'SELL' && rec.position_size > 0 && (
                <p><strong>Quantity to Sell:</strong> {rec.position_size} shares</p>
              )}
            </div>

            <div className="detail-section">
              <h4>Analysis Breakdown</h4>
              {rec.analysis_breakdown && (
                <>
                  {rec.analysis_breakdown.regime_switching && (
                    <div className="analysis-item">
                      <strong>Regime Analysis:</strong>
                      <span> {rec.analysis_breakdown.regime_switching.regime}</span>
                      <span className="detail-badge">
                        {(rec.analysis_breakdown.regime_switching.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  )}
                  {rec.analysis_breakdown.walk_forward && (
                    <div className="analysis-item">
                      <strong>Walk-Forward:</strong>
                      <span> Expected Return: {(rec.analysis_breakdown.walk_forward.expected_return * 100).toFixed(2)}%</span>
                      <span className="detail-badge">
                        Sharpe: {rec.analysis_breakdown.walk_forward.sharpe_ratio.toFixed(2)}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {rec.reasoning && rec.reasoning.length > 0 && (
              <div className="detail-section">
                <h4>Reasoning</h4>
                {rec.reasoning.map((reason, idx) => (
                  <p key={idx} className="reasoning-item">{reason}</p>
                ))}
              </div>
            )}

            {rec.warnings && rec.warnings.length > 0 && (
              <div className="detail-section warnings">
                <h4>⚠️ Warnings</h4>
                {rec.warnings.map((warning, idx) => (
                  <p key={idx} className="warning-text">{warning}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="analysis-results">
      <div className="results-header">
        <h2>📊 Analysis Results</h2>
        <div className="results-summary">
          <span className="summary-item buy">
            🟢 {summary.buy_signals} Buy
          </span>
          <span className="summary-item sell">
            🔴 {summary.sell_signals} Sell
          </span>
          <span className="summary-item hold">
            🟡 {summary.hold_signals} Hold
          </span>
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${selectedTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setSelectedTab('recommendations')}
        >
          All Recommendations
        </button>
        <button
          className={`tab ${selectedTab === 'buy' ? 'active' : ''}`}
          onClick={() => setSelectedTab('buy')}
        >
          Buy Signals ({buy_recommendations.length})
        </button>
        <button
          className={`tab ${selectedTab === 'sell' ? 'active' : ''}`}
          onClick={() => setSelectedTab('sell')}
        >
          Sell Signals ({sell_recommendations.length})
        </button>
      </div>

      <div className="recommendations-list">
        {selectedTab === 'recommendations' &&
          [...buy_recommendations, ...sell_recommendations, ...hold_recommendations].map(renderRecommendationCard)
        }
        {selectedTab === 'buy' &&
          (buy_recommendations.length > 0
            ? buy_recommendations.map(renderRecommendationCard)
            : <div className="no-results">No buy signals</div>)
        }
        {selectedTab === 'sell' &&
          (sell_recommendations.length > 0
            ? sell_recommendations.map(renderRecommendationCard)
            : <div className="no-results">No sell signals</div>)
        }
      </div>
    </div>
  );
}

export default AnalysisResults;
