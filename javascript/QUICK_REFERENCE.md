# Quick Reference Guide

## File Organization

```
src/
├── App.jsx                    # Main app component (530 lines)
├── components/                # Pure UI components
│   ├── FloatingMenu.jsx       # Menu buttons
│   ├── SettingsPanel.jsx      # Settings UI
│   ├── LogsPanel.jsx          # Logs display
│   ├── RegionBox.jsx          # Region editor
│   ├── TranslationOverlay.jsx # Translation display
│   ├── SelectionBox.jsx       # Selection visualizer
│   └── LoadingIndicator.jsx   # Status display
├── hooks/                      # Business logic
│   ├── useOCR.js              # Tesseract integration
│   ├── useTranslation.js      # Translation APIs
│   ├── useImageProcessing.js  # Image enhancement
│   └── useTextFiltering.js    # Text validation
└── utils/                      # Shared utilities
    ├── constants.js           # Config & constants
    └── storage.js             # LocalStorage wrapper
```

## Component Quick Reference

### FloatingMenu

```jsx
<FloatingMenu
  isMenuOpen={isMenuOpen}
  onToggle={() => setIsMenuOpen(!isMenuOpen)}
  onTranslate={triggerAction}
  onSettings={() => setShowSettings(!showSettings)}
  onLogs={() => setShowLogs(!showLogs)}
  onClear={clearAll}
  onMouseEnter={handleMouseEnterUI}
  onMouseLeave={handleMouseLeaveUI}
/>
```

### SettingsPanel

```jsx
<SettingsPanel
  mode={mode}
  provider={provider}
  apiKey={apiKey}
  sourceLang={sourceLang}
  targetLang={targetLang}
  styleSettings={styleSettings}
  onModeChange={setMode}
  onProviderChange={setProvider}
  onApiKeyChange={setApiKey}
  onSourceLangChange={setSourceLang}
  onTargetLangChange={setTargetLang}
  onStyleChange={setStyleSettings}
  onAdjustRegion={startEditingRegion}
  onClose={() => setShowSettings(false)}
  onMouseEnter={handleMouseEnterUI}
/>
```

### LogsPanel

```jsx
<LogsPanel
  logs={logs}
  debugImage={debugImage}
  onClearLogs={() => setLogs([])}
  onClose={() => setShowLogs(false)}
  onMouseEnter={handleMouseEnterUI}
/>
```

### RegionBox

```jsx
<RegionBox
  regionRect={regionRect}
  onResizeStart={handleResizeStart}
  onSave={saveRegion}
  onCancel={cancelRegion}
  onMouseEnter={handleMouseEnterUI}
  onMouseLeave={handleMouseLeaveUI}
/>
```

### TranslationOverlay

```jsx
<TranslationOverlay
  translations={translations}
  styleSettings={styleSettings}
  onMouseEnter={handleMouseEnterUI}
/>
```

## Hook Usage Examples

### useOCR

```jsx
const { recognizeText, extractTextBlocks } = useOCR();

// Recognize text in image
const result = await recognizeText(imageData, 'eng', progress => {
  console.log(`OCR: ${progress}%`);
});

// Extract text blocks from OCR result
const textBlocks = extractTextBlocks(result);
```

### useTranslation

```jsx
const { translateMyMemory, translateDeepL } = useTranslation();

// Free translation
const translated = await translateMyMemory('hello', 'eng', 'por');

// DeepL translation
const translated = await translateDeepL('hello', 'eng', 'por', apiKey);
```

### useImageProcessing

```jsx
const { preprocessImage } = useImageProcessing();

// Preprocess image for OCR
const processed = await preprocessImage(imageDataUrl, regionRect);
```

### useTextFiltering

```jsx
const { isValidText } = useTextFiltering();

// Check if text is valid
if (isValidText(detectedText, minLength)) {
  // Process text
}
```

## Constants Reference

### LANGUAGES

```javascript
[
  { code: 'eng', label: 'English', tesseract: 'eng' },
  { code: 'por', label: 'Portuguese', tesseract: 'por' },
  // ... more languages
];
```

### PROVIDERS

```javascript
[
  { id: 'mymemory', name: 'MyMemory (Free)', requiresKey: false },
  { id: 'deepl', name: 'DeepL API', requiresKey: true },
];
```

### OCR_CONFIG

```javascript
{
  CONFIDENCE_THRESHOLD: 40,      // Min word confidence %
  MIN_WORD_LENGTH: 2,            // Min characters
  MIN_WORD_SIZE: 8,              // Min pixel size
  MIN_TEXT_LENGTH: 3,            // Min block text
  ASPECT_RATIO_MIN: 0.3,         // Width/height min
  ASPECT_RATIO_MAX: 4,           // Width/height max
  UNIQUENESS_RATIO_MIN: 0.3,     // Unique char ratio
  LINE_CONFIDENCE_THRESHOLD: 20,  // Fallback threshold
  IMAGE_SCALE: 3,                // Upscaling factor
}
```

## State Management in App.jsx

### Translation State

```javascript
const [translations, setTranslations] = useState([]);
const [isProcessing, setIsProcessing] = useState(false);
const [status, setStatus] = useState('');
```

### UI State

```javascript
const [isMenuOpen, setIsMenuOpen] = useState(false);
const [showSettings, setShowSettings] = useState(false);
const [showLogs, setShowLogs] = useState(false);
```

### Settings

```javascript
const [sourceLang, setSourceLang] = useState(...);
const [targetLang, setTargetLang] = useState(...);
const [mode, setMode] = useState(...); // 'crop', 'global', 'brush'
const [provider, setProvider] = useState(...); // 'mymemory', 'deepl'
const [apiKey, setApiKey] = useState(...);
const [styleSettings, setStyleSettings] = useState(...);
```

### Region State

```javascript
const [regionRect, setRegionRect] = useState(...);
const [tempRegionRect, setTempRegionRect] = useState(null);
const [isEditingRegion, setIsEditingRegion] = useState(false);
const [isDraggingRegion, setIsDraggingRegion] = useState(false);
const [isResizingRegion, setIsResizingRegion] = useState(false);
```

## Common Tasks

### Add a new language

1. Open `src/utils/constants.js`
2. Add entry to LANGUAGES array:

```javascript
{ code: 'deu', label: 'German', tesseract: 'deu' }
```

### Add a new translation provider

1. Open `src/hooks/useTranslation.js`
2. Add new translation function
3. Update `processTranslation` in App.jsx to use it

### Adjust OCR quality

1. Open `src/utils/constants.js`
2. Modify OCR_CONFIG values
3. All hooks using config will auto-update

### Change UI appearance

1. Modify component in `src/components/`
2. Or update style in `src/index.css`

### Debug OCR results

1. Open Logs panel
2. View debug image showing processed OCR input
3. Check console for full OCR data

## Testing Hooks

```javascript
// Test OCR hook
import { renderHook, act } from '@testing-library/react-hooks';
import { useOCR } from './hooks/useOCR';

test('useOCR should recognize text', () => {
  const { result } = renderHook(() => useOCR());
  // Test logic here
});
```

## Performance Tips

1. **Lazy load heavy components** - Components are already split
2. **Memoize expensive operations** - useOCR results can be cached
3. **Use React DevTools** - Profile component rendering
4. **Monitor hook dependencies** - Avoid unnecessary recalculations

## Debugging Tips

1. **Check constants.js** - Most config is here
2. **Inspect hooks** - Business logic in hooks/
3. **Review components** - UI code in components/
4. **Check App.jsx** - State and orchestration
5. **Use browser console** - Lots of console.logs for debugging

## Import Examples

```javascript
// Import constants
import { LANGUAGES, PROVIDERS, OCR_CONFIG } from './utils/constants';

// Import hooks
import { useOCR } from './hooks/useOCR';
import { useTranslation } from './hooks/useTranslation';

// Import components
import FloatingMenu from './components/FloatingMenu';
import SettingsPanel from './components/SettingsPanel';

// Import utilities
import { loadState, saveState } from './utils/storage';
```

## Key App.jsx Functions

### Main Pipeline

```javascript
processTranslation(rect) {
  1. Capture screen
  2. Preprocess image
  3. Run OCR
  4. Extract text blocks
  5. Translate text
  6. Display results
}
```

### Event Handlers

```javascript
triggerAction(); // Start translation
handleMouseDown / Up / Move(); // User interaction
startEditingRegion(); // Edit region
saveRegion(); // Save region changes
clearAll(); // Reset everything
```

## Support

For questions about the architecture, see:

- `ARCHITECTURE.md` - Detailed architecture overview
- `COMPONENTIZATION_SUMMARY.md` - Before/after comparison
- Source code comments in hooks and components
