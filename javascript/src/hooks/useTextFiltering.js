// hooks/useTextFiltering.js

const FAUX_PATTERNS = [
  /^[.\-_\s]+$/, // Only punctuation/spaces
  /^[0-9]+$/, // Only numbers
  /^[^a-zA-Z0-9àáâãäåèéêëìíîïòóôõöùúûüçñ]*$/, // No letters/accents
  /[\u0080-\uFFFF]{2,}/, // Too many special unicode
];

export const useTextFiltering = () => {
  const isValidText = (text, minLength = 3) => {
    if (text.length < minLength) return false;
    if (FAUX_PATTERNS.some(p => p.test(text))) return false;
    return true;
  };

  return {
    isValidText,
    FAUX_PATTERNS,
  };
};
