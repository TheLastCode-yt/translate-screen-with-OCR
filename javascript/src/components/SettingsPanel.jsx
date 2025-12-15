// components/SettingsPanel.jsx
import React from 'react';
import { LANGUAGES, PROVIDERS } from '../utils/constants';

function SettingsPanel({
  mode,
  provider,
  apiKey,
  sourceLang,
  targetLang,
  styleSettings,
  onModeChange,
  onProviderChange,
  onApiKeyChange,
  onSourceLangChange,
  onTargetLangChange,
  onStyleChange,
  onAdjustRegion,
  onClose,
  onMouseEnter,
}) {
  return (
    <div
      className="settings-panel"
      onMouseDown={e => e.stopPropagation()}
      onMouseEnter={onMouseEnter}
    >
      <h3>Settings</h3>

      <div className="setting-group">
        <label>Mode:</label>
        <div className="mode-selector">
          <button
            className={mode === 'crop' ? 'active' : ''}
            onClick={() => onModeChange('crop')}
          >
            Region
          </button>
          <button
            className={mode === 'global' ? 'active' : ''}
            onClick={() => onModeChange('global')}
          >
            Global
          </button>
          <button
            className={mode === 'brush' ? 'active' : ''}
            onClick={() => onModeChange('brush')}
          >
            Brush
          </button>
        </div>
        {mode === 'crop' && (
          <button
            className="adjust-region-btn"
            onClick={onAdjustRegion}
            style={{
              marginTop: 10,
              width: '100%',
              padding: 5,
              cursor: 'pointer',
            }}
          >
            Adjust Region Area
          </button>
        )}
      </div>

      <div className="setting-group">
        <label>Translation Provider:</label>
        <select
          value={provider}
          onChange={e => onProviderChange(e.target.value)}
        >
          {PROVIDERS.map(p => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {provider === 'deepl' && (
        <div className="setting-group">
          <label>DeepL API Key:</label>
          <input
            type="password"
            value={apiKey}
            onChange={e => onApiKeyChange(e.target.value)}
            placeholder="Paste your API Key here"
          />
          <small style={{ fontSize: 10, color: '#999' }}>
            Key usually ends with :fx for free tier
          </small>
        </div>
      )}

      <div className="setting-group">
        <label>Language:</label>
        <div style={{ display: 'flex', gap: 5 }}>
          <select
            value={sourceLang.code}
            onChange={e => {
              const lang = LANGUAGES.find(l => l.code === e.target.value);
              onSourceLangChange(lang);
            }}
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>
                {l.code.toUpperCase()}
              </option>
            ))}
          </select>
          <span>➡</span>
          <select
            value={targetLang.code}
            onChange={e => {
              const lang = LANGUAGES.find(l => l.code === e.target.value);
              onTargetLangChange(lang);
            }}
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>
                {l.code.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="setting-group">
        <label>Background:</label>
        <div className="color-palette">
          {['#ffffff', '#000000', '#1a1a1a', '#fffae3', '#e3f2fd'].map(c => (
            <div
              key={c}
              className={`color-swatch ${
                styleSettings.backgroundColor === c ? 'active' : ''
              }`}
              style={{
                background: c,
                border: c === '#ffffff' ? '1px solid #ddd' : 'none',
              }}
              onClick={() =>
                onStyleChange({ ...styleSettings, backgroundColor: c })
              }
            />
          ))}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            marginTop: 5,
          }}
        >
          <span style={{ fontSize: 10 }}>Opacity:</span>
          <input
            type="range"
            min="0.5"
            max="1"
            step="0.1"
            value={styleSettings.bgOpacity}
            onChange={e =>
              onStyleChange({
                ...styleSettings,
                bgOpacity: parseFloat(e.target.value),
              })
            }
          />
        </div>
      </div>

      <div className="setting-group">
        <label>Text Color:</label>
        <div className="color-palette">
          {['#000000', '#ffffff', '#ffff00', '#00ff00', '#ff0000'].map(c => (
            <div
              key={c}
              className={`color-swatch ${
                styleSettings.color === c ? 'active' : ''
              }`}
              style={{
                background: c,
                border: c === '#ffffff' ? '1px solid #ddd' : 'none',
              }}
              onClick={() => onStyleChange({ ...styleSettings, color: c })}
            />
          ))}
        </div>
      </div>

      <div className="setting-group">
        <label>Font Size: {styleSettings.fontSize}px</label>
        <input
          type="range"
          min="10"
          max="30"
          value={styleSettings.fontSize}
          onChange={e =>
            onStyleChange({
              ...styleSettings,
              fontSize: parseInt(e.target.value),
            })
          }
        />
      </div>

      <button onClick={onClose} style={{ marginTop: 10, width: '100%' }}>
        Close
      </button>
    </div>
  );
}

export default SettingsPanel;
