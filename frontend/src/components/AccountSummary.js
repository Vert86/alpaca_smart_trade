import React from 'react';
import './AccountSummary.css';

function AccountSummary({ account, positions, riskSummary }) {
  if (!account) {
    return (
      <div className="card account-summary">
        <h3>💼 Account Summary</h3>
        <div className="loading-account">Loading account data...</div>
      </div>
    );
  }

  const portfolio = riskSummary?.portfolio || {};
  const pdt = riskSummary?.pdt || {};

  return (
    <div className="card account-summary">
      <h3>💼 Account Summary</h3>

      <div className="account-stats">
        <div className="stat-item">
          <span className="stat-label">Equity</span>
          <span className="stat-value">${account.equity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Cash</span>
          <span className="stat-value">${account.cash?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Buying Power</span>
          <span className="stat-value">${account.buying_power?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      <div className="portfolio-metrics">
        <h4>Portfolio Metrics</h4>

        <div className="metric-row">
          <span>Positions</span>
          <span className="metric-value">{positions?.length || 0}</span>
        </div>

        <div className="metric-row">
          <span>Total P/L</span>
          <span className={`metric-value ${portfolio.total_unrealized_pl >= 0 ? 'positive' : 'negative'}`}>
            ${portfolio.total_unrealized_pl?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            {portfolio.total_unrealized_pl_pct !== undefined && (
              <> ({portfolio.total_unrealized_pl_pct > 0 ? '+' : ''}{portfolio.total_unrealized_pl_pct}%)</>
            )}
          </span>
        </div>

        <div className="metric-row">
          <span>Invested</span>
          <span className="metric-value">
            ${riskSummary?.account?.invested?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            {riskSummary?.account?.invested_percentage !== undefined && (
              <> ({riskSummary.account.invested_percentage}%)</>
            )}
          </span>
        </div>
      </div>

      <div className="pdt-status">
        <h4>PDT Status</h4>
        <div className="pdt-info">
          <span>Day Trades: {pdt.daytrade_count || 0}/3</span>
          {pdt.pdt_restricted && (
            <span className="pdt-warning">⚠️ PDT RESTRICTED</span>
          )}
        </div>
      </div>

      {riskSummary?.warnings && riskSummary.warnings.length > 0 && (
        <div className="warnings-section">
          <h4>⚠️ Warnings</h4>
          {riskSummary.warnings.map((warning, idx) => (
            <div key={idx} className="warning-item">{warning}</div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AccountSummary;
