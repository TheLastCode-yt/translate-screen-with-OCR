// hooks/useImageProcessing.js
import { OCR_CONFIG } from '../utils/constants';

const log = (message, data = null) => {
  const timestamp = new Date().toLocaleTimeString('pt-BR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
  if (data) {
    console.log(`[${timestamp}] 📸 ImageProcessing: ${message}`, data);
  } else {
    console.log(`[${timestamp}] 📸 ImageProcessing: ${message}`);
  }
};

export const useImageProcessing = () => {
  const preprocessImage = (dataUrl, rect) => {
    return new Promise((resolve, reject) => {
      try {
        log('Iniciando preprocessamento de imagem', {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
        });

        const img = new Image();
        img.onload = () => {
          try {
            const scale = OCR_CONFIG.IMAGE_SCALE;
            log(`Escala configurada: ${scale}x`);

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = rect.width * scale;
            canvas.height = rect.height * scale;
            log(`Canvas criado: ${canvas.width}x${canvas.height}px`);

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
            log('Imagem desenhada no canvas');

            // Apply image enhancement for better OCR
            const imageData = ctx.getImageData(
              0,
              0,
              canvas.width,
              canvas.height
            );
            const data = imageData.data;
            log('Dados de imagem extraídos');

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
            log(`Análise de contraste: min=${minGray}, max=${maxGray}`);

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
            log('Contraste aplicado e imagem convertida para PNG');

            const dataUrl = canvas.toDataURL('image/png');
            log(`✅ Preprocessamento concluído (${dataUrl.length} bytes)`);
            resolve(dataUrl);
          } catch (error) {
            log('❌ Erro durante o preprocessamento', error.message);
            reject(error);
          }
        };
        img.onerror = () => {
          const error = new Error(
            'Falha ao carregar imagem para processamento'
          );
          log('❌ Erro ao carregar imagem', error.message);
          reject(error);
        };
        img.src = dataUrl;
      } catch (error) {
        log('❌ Erro ao inicializar preprocessamento', error.message);
        reject(error);
      }
    });
  };

  return { preprocessImage };
};
