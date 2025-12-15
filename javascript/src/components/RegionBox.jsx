// components/RegionBox.jsx
import React from 'react';

function RegionBox({
  regionRect,
  onResizeStart,
  onSave,
  onCancel,
  onMouseEnter,
  onMouseLeave,
}) {
  return (
    <div
      className="region-box"
      style={{
        left: regionRect.x,
        top: regionRect.y,
        width: regionRect.width,
        height: regionRect.height,
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="region-box-border"></div>
      <div className="region-handle" onMouseDown={onResizeStart}>
        ↘
      </div>
      <div className="region-label">Adjust Region</div>
      <div className="region-controls">
        <button className="region-btn confirm" onClick={onSave} title="Save">
          ✔
        </button>
        <button className="region-btn cancel" onClick={onCancel} title="Cancel">
          ✖
        </button>
      </div>
    </div>
  );
}

export default RegionBox;
