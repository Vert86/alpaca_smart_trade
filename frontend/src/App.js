import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import AccountSummary from './components/AccountSummary';
import StockSelector from './components/StockSelector';
import AnalysisResults from './components/AnalysisResults';
import TradingPanel from './components/TradingPanel';
import LoadingSpinner from './components/LoadingSpinner';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function App() {
  const [account, setAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [riskSummary, setRiskSummary] = useState(null);
  const [selectedSymbols, setSelectedSymbols] = useState([
    'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'UNH', 'CRWD', 'V', 'ASML', 'PLTR'
  ]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);
  const [telegramStatus, setTelegramStatus] = useState('');

  // Load account data on mount
  useEffect(() => {
    loadAccountData();
    loadConfig();
  }, []);

  const loadAccountData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/account`);
      if (response.data.success) {
        setAccount(response.data.account);
        setPositions(response.data.positions);
        setRiskSummary(response.data.risk_summary);
      }
    } catch (err) {
      console.error('Failed to load account data:', err);
      setError('Failed to load account data. Please check your Alpaca API credentials.');
    }
  };

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config`);
      if (response.data.success) {
        setConfig(response.data.config);
      }
    } catch (err) {
      console.error('Failed to load config:', err);
    }
  };

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    setTelegramStatus('');

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, {
        symbols: selectedSymbols,
        lookback_days: config?.lookback_days || 60
      });

      if (response.data.success) {
        setAnalysisResults(response.data);
        setAccount(response.data.account);
        setRiskSummary(response.data.risk_summary);
      } else {
        setError(response.data.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.response?.data?.error || 'Failed to run analysis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sendToTelegram = async () => {
    if (!analysisResults) {
      setTelegramStatus('error:No analysis results to send');
      return;
    }

    try {
      setTelegramStatus('sending');
      const response = await axios.post(`${API_BASE_URL}/send-telegram`, {
        analysis: analysisResults.analysis
      });

      if (response.data.success) {
        setTelegramStatus('success');
        setTimeout(() => setTelegramStatus(''), 3000);
      } else {
        setTelegramStatus(`error:${response.data.error}`);
      }
    } catch (err) {
      console.error('Telegram error:', err);
      setTelegramStatus(`error:${err.response?.data?.error || 'Failed to send to Telegram'}`);
    }
  };

  const executeTrade = async (tradeDetails) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/execute-trade`, tradeDetails);

      if (response.data.success) {
        // Refresh account and positions
        await loadAccountData();
        return { success: true, order: response.data.order };
      } else {
        return { success: false, error: response.data.error };
      }
    } catch (err) {
      console.error('Trade execution error:', err);
      return {
        success: false,
        error: err.response?.data?.error || 'Failed to execute trade'
      };
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>📊 Alpaca Smart Trade</h1>
          <p className="tagline">Intelligent Trading Analysis & Automation</p>
          {config?.paper_trading && (
            <span className="paper-trading-badge">PAPER TRADING</span>
          )}
        </div>
      </header>

      <div className="main-container">
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="close-btn">✕</button>
          </div>
        )}

        <div className="dashboard">
          {/* Left Panel: Account & Settings */}
          <div className="left-panel">
            <AccountSummary
              account={account}
              positions={positions}
              riskSummary={riskSummary}
            />

            <StockSelector
              selectedSymbols={selectedSymbols}
              onSymbolsChange={setSelectedSymbols}
            />

            <div className="action-panel">
              <button
                className="btn btn-primary btn-large"
                onClick={runAnalysis}
                disabled={loading || selectedSymbols.length === 0}
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="small" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    🔍 Run Analysis
                  </>
                )}
              </button>

              {analysisResults && (
                <button
                  className="btn btn-telegram"
                  onClick={sendToTelegram}
                  disabled={!config?.telegram_configured || telegramStatus === 'sending'}
                >
                  {telegramStatus === 'sending' && <LoadingSpinner size="small" />}
                  {telegramStatus === 'success' && '✅ Sent!'}
                  {telegramStatus.startsWith('error:') && '❌ Failed'}
                  {!telegramStatus && (
                    config?.telegram_configured
                      ? '📱 Send to Telegram'
                      : '📱 Telegram Not Configured'
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Right Panel: Analysis Results */}
          <div className="right-panel">
            {loading && (
              <div className="loading-container">
                <LoadingSpinner />
                <h3>Analyzing {selectedSymbols.length} stocks...</h3>
                <p>Running walk-forward optimization and regime-switching analysis</p>
              </div>
            )}

            {!loading && !analysisResults && (
              <div className="empty-state">
                <div className="empty-icon">📈</div>
                <h2>Ready to Analyze</h2>
                <p>Select your stocks and click "Run Analysis" to get started</p>
                <div className="features-list">
                  <div className="feature-item">
                    <span className="feature-icon">🎯</span>
                    <span>Walk-Forward Optimization</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">📊</span>
                    <span>Regime-Switching Indicators</span>
                  </div>
                  <div className="feature-item">
                    <span className="feature-icon">🛡️</span>
                    <span>Risk Management & PDT Protection</span>
                  </div>
                </div>
              </div>
            )}

            {!loading && analysisResults && (
              <>
                <AnalysisResults
                  results={analysisResults}
                />
                <TradingPanel
                  results={analysisResults}
                  onExecuteTrade={executeTrade}
                  onRefresh={loadAccountData}
                />
              </>
            )}
          </div>
        </div>
      </div>

      <footer className="app-footer">
        <p>⚠️ This is an automated trading tool. Always review recommendations before executing trades.</p>
        <p className="footer-note">Powered by Alpaca Markets API</p>
      </footer>
    </div>
  );
}

export default App;
