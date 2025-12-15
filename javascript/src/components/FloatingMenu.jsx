// components/FloatingMenu.jsx
import React from 'react';

function FloatingMenu({
  isMenuOpen,
  onToggle,
  onTranslate,
  onSettings,
  onLogs,
  onClear,
  onMouseEnter,
  onMouseLeave,
}) {
  return (
    <div
      className="floating-menu-container"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <button
        className={`main-toggle-btn ${isMenuOpen ? 'open' : ''}`}
        onClick={onToggle}
        title="Menu"
      >
        文
      </button>

      {isMenuOpen && (
        <div className="menu-options">
          <button
            className="menu-btn"
            onClick={onTranslate}
            title="Translate (Ctrl+Z)"
          >
            ▶
          </button>
          <button className="menu-btn" onClick={onSettings} title="Settings">
            ⚙
          </button>
          <button className="menu-btn" onClick={onLogs} title="Logs">
            📋
          </button>
          <button
            className="menu-btn close-btn"
            onClick={onClear}
            title="Clear / Close"
          >
            ✖
          </button>
        </div>
      )}
    </div>
  );
}

export default FloatingMenu;
