// components/LoadingIndicator.jsx
import React from 'react';

function LoadingIndicator({ status }) {
  return <div className="loading">{status}</div>;
}

export default LoadingIndicator;
