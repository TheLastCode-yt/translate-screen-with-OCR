// hooks/useTextFiltering.js

const log = (message, data = null) => {
  const timestamp = new Date().toLocaleTimeString('pt-BR', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
  if (data) {
    console.log(`[${timestamp}] 🚫 TextFilter: ${message}`, data);
  } else {
    console.log(`[${timestamp}] 🚫 TextFilter: ${message}`);
  }
};

const FAUX_PATTERNS = [
  /^[.\-_\s]+$/, // Only punctuation/spaces
  /^[0-9]+$/, // Only numbers
  /^[^a-zA-Z0-9àáâãäåèéêëìíîïòóôõöùúûüçñ]*$/, // No letters/accents
  /[\u0080-\uFFFF]{2,}/, // Too many special unicode
];

const PATTERN_NAMES = [
  'Apenas pontuação/espaços',
  'Apenas números',
  'Sem letras ou acentos',
  'Unicode especial demais',
];

export const useTextFiltering = () => {
  const isValidText = (text, minLength = 3) => {
    // Check minimum length
    if (text.length < minLength) {
      log(`❌ Texto muito curto`, {
        texto: text,
        comprimento: text.length,
        minimo: minLength,
      });
      return false;
    }

    // Check against faux patterns
    for (let i = 0; i < FAUX_PATTERNS.length; i++) {
      if (FAUX_PATTERNS[i].test(text)) {
        log(`⏭️ Texto filtrado: ${PATTERN_NAMES[i]}`, {
          texto: text,
          padrao: i + 1,
        });
        return false;
      }
    }

    log(`✅ Texto válido`, {
      texto: text.substring(0, 50),
      comprimento: text.length,
    });
    return true;
  };

  return {
    isValidText,
    FAUX_PATTERNS,
  };
};
