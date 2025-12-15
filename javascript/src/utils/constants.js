// Language Options
export const LANGUAGES = [
  { code: 'eng', label: 'English', tesseract: 'eng' },
  { code: 'por', label: 'Portuguese', tesseract: 'por' },
  { code: 'spa', label: 'Spanish', tesseract: 'spa' },
  { code: 'fra', label: 'French', tesseract: 'fra' },
  { code: 'deu', label: 'German', tesseract: 'deu' },
  { code: 'jpn', label: 'Japanese', tesseract: 'jpn' },
];

export const PROVIDERS = [
  { id: 'mymemory', name: 'MyMemory (Free)', requiresKey: false },
  { id: 'deepl', name: 'DeepL API', requiresKey: true },
];

export const OCR_CONFIG = {
  CONFIDENCE_THRESHOLD: 40,
  MIN_WORD_LENGTH: 2,
  MIN_WORD_SIZE: 8,
  MIN_TEXT_LENGTH: 3,
  ASPECT_RATIO_MIN: 0.3,
  ASPECT_RATIO_MAX: 4,
  UNIQUENESS_RATIO_MIN: 0.3,
  LINE_CONFIDENCE_THRESHOLD: 20,
  IMAGE_SCALE: 3,
};

export const DEFAULT_REGION = { x: 100, y: 100, width: 300, height: 200 };

export const DEFAULT_STYLE_SETTINGS = {
  backgroundColor: '#ffffff',
  bgOpacity: 0.9,
  color: '#000000',
  fontSize: 14,
};
