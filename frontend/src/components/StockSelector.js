import React, { useState } from 'react';
import './StockSelector.css';

const DEFAULT_STOCKS = [
  'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'TSLA',
  'UNH', 'CRWD', 'V', 'ASML', 'PLTR'
];

function StockSelector({ selectedSymbols, onSymbolsChange }) {
  const [customSymbol, setCustomSymbol] = useState('');

  const toggleSymbol = (symbol) => {
    if (selectedSymbols.includes(symbol)) {
      onSymbolsChange(selectedSymbols.filter(s => s !== symbol));
    } else {
      onSymbolsChange([...selectedSymbols, symbol]);
    }
  };

  const addCustomSymbol = () => {
    const symbol = customSymbol.trim().toUpperCase();
    if (symbol && !selectedSymbols.includes(symbol)) {
      onSymbolsChange([...selectedSymbols, symbol]);
      setCustomSymbol('');
    }
  };

  const selectAll = () => {
    onSymbolsChange([...DEFAULT_STOCKS]);
  };

  const clearAll = () => {
    onSymbolsChange([]);
  };

  return (
    <div className="card stock-selector">
      <h3>📈 Stock Selection</h3>

      <div className="selector-actions">
        <button className="btn-small" onClick={selectAll}>Select All</button>
        <button className="btn-small" onClick={clearAll}>Clear All</button>
      </div>

      <div className="stock-grid">
        {DEFAULT_STOCKS.map(symbol => (
          <button
            key={symbol}
            className={`stock-chip ${selectedSymbols.includes(symbol) ? 'selected' : ''}`}
            onClick={() => toggleSymbol(symbol)}
          >
            {symbol}
          </button>
        ))}
      </div>

      <div className="custom-symbol-input">
        <input
          type="text"
          placeholder="Add custom symbol..."
          value={customSymbol}
          onChange={(e) => setCustomSymbol(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addCustomSymbol()}
        />
        <button className="btn-add" onClick={addCustomSymbol}>+</button>
      </div>

      <div className="selection-summary">
        {selectedSymbols.length} stock{selectedSymbols.length !== 1 ? 's' : ''} selected
      </div>
    </div>
  );
}

export default StockSelector;
