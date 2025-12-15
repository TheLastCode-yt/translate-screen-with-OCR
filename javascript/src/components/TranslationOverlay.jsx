// components/TranslationOverlay.jsx
import React from 'react';

function TranslationOverlay({ translations, styleSettings, onMouseEnter }) {
  return (
    <div className="overlay-container">
      {translations.map((item, index) => {
        const boxWidth = Math.max(item.bbox.x1 - item.bbox.x0, 50);
        const boxHeight = Math.max(item.bbox.y1 - item.bbox.y0, 20);

        return (
          <div
            key={index}
            className="translation-box"
            style={{
              left: `${item.bbox.x0}px`,
              top: `${item.bbox.y0}px`,
              width: `${boxWidth}px`,
              minHeight: `${boxHeight}px`,
              backgroundColor: styleSettings.backgroundColor,
              color: styleSettings.color,
              fontSize: `${styleSettings.fontSize}px`,
              opacity: styleSettings.bgOpacity,
            }}
            title={item.original}
            onMouseEnter={onMouseEnter}
          >
            {item.text}
          </div>
        );
      })}
    </div>
  );
}

export default TranslationOverlay;
