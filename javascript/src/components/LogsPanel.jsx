// components/LogsPanel.jsx
import React from 'react';

function LogsPanel({ logs, debugImage, onClearLogs, onClose, onMouseEnter }) {
  return (
    <div
      className="logs-panel"
      onMouseDown={e => e.stopPropagation()}
      onMouseEnter={onMouseEnter}
    >
      <h3>Translation Logs</h3>
      <div className="logs-list">
        {logs.length === 0 ? (
          <p style={{ color: '#999', textAlign: 'center' }}>No logs yet.</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="log-item">
              <div className="log-time">
                {log.timestamp}{' '}
                <span
                  style={{
                    fontSize: 9,
                    background: '#eee',
                    padding: '1px 3px',
                    borderRadius: 3,
                  }}
                >
                  {log.provider}
                </span>
              </div>
              <div className="log-original">
                <strong>Detected:</strong> {log.original}
              </div>
              <div className="log-translated">
                <strong>Translated:</strong> {log.translated}
              </div>
            </div>
          ))
        )}
      </div>
      <button
        onClick={onClearLogs}
        style={{
          marginTop: 10,
          width: '100%',
          background: '#ff4646',
          color: 'white',
          border: 'none',
          padding: 5,
          borderRadius: 4,
          cursor: 'pointer',
        }}
      >
        Clear Logs
      </button>

      {debugImage && (
        <div style={{ marginTop: 10 }}>
          <label style={{ fontSize: 11, color: '#999' }}>
            Last Captured Image (Debug):
          </label>
          <img
            src={debugImage}
            style={{
              width: '100%',
              border: '1px solid #ddd',
              marginTop: 5,
            }}
          />
        </div>
      )}

      <button onClick={onClose} style={{ marginTop: 5, width: '100%' }}>
        Close
      </button>
    </div>
  );
}

export default LogsPanel;
