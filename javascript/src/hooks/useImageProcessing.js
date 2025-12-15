// hooks/useImageProcessing.js
import { OCR_CONFIG } from '../utils/constants';

export const useImageProcessing = () => {
  const preprocessImage = (dataUrl, rect) => {
    return new Promise(resolve => {
      const img = new Image();
      img.onload = () => {
        const scale = OCR_CONFIG.IMAGE_SCALE;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = rect.width * scale;
        canvas.height = rect.height * scale;

        // Draw the cropped area scaled up
        ctx.drawImage(
          img,
          rect.x,
          rect.y,
          rect.width,
          rect.height,
          0,
          0,
          canvas.width,
          canvas.height
        );

        // Apply image enhancement for better OCR
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        // Convert to grayscale and enhance contrast aggressively
        let minGray = 255;
        let maxGray = 0;

        // First pass: find min and max for normalization
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];
          const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
          minGray = Math.min(minGray, gray);
          maxGray = Math.max(maxGray, gray);
        }

        // Second pass: normalize and enhance contrast aggressively
        const range = maxGray - minGray || 1;
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];

          // Convert to grayscale
          const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);

          // Normalize contrast
          const normalized = ((gray - minGray) / range) * 255;

          // Apply stronger contrast enhancement for better OCR
          const enhanced = normalized > 128 ? 255 : 0;

          data[i] = enhanced; // R
          data[i + 1] = enhanced; // G
          data[i + 2] = enhanced; // B
        }

        ctx.putImageData(imageData, 0, 0);
        resolve(canvas.toDataURL('image/png'));
      };
      img.src = dataUrl;
    });
  };

  return { preprocessImage };
};
