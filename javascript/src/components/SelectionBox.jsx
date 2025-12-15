// components/SelectionBox.jsx
import React from 'react';

function SelectionBox({ selectionRect }) {
  return (
    <div
      className="selection-box"
      style={{
        left: selectionRect.x,
        top: selectionRect.y,
        width: selectionRect.width,
        height: selectionRect.height,
      }}
    />
  );
}

export default SelectionBox;
