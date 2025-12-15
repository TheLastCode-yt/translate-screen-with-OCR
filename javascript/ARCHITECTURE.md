# Translate App - Component Architecture

## Overview

The application has been refactored into a modular, component-driven architecture with clear separation of concerns. This makes the codebase more maintainable, testable, and reusable.

## Project Structure

```
src/
├── components/           # Reusable UI Components
│   ├── FloatingMenu.jsx
│   ├── SettingsPanel.jsx
│   ├── LogsPanel.jsx
│   ├── RegionBox.jsx
│   ├── TranslationOverlay.jsx
│   ├── SelectionBox.jsx
│   └── LoadingIndicator.jsx
├── hooks/               # Business Logic & State Management
│   ├── useOCR.js
│   ├── useTranslation.js
│   ├── useImageProcessing.js
│   └── useTextFiltering.js
├── utils/               # Utilities & Constants
│   ├── constants.js
│   └── storage.js
├── App.jsx              # Main Application Component
├── main.jsx
└── index.css
```

## Component Details

### Components (UI Layer)

#### FloatingMenu.jsx

- Renders the main toggle button and menu options
- Props: isMenuOpen, onToggle, onTranslate, onSettings, onLogs, onClear

#### SettingsPanel.jsx

- Displays all settings (mode, provider, language, appearance)
- Manages mode selection, API key input, color customization
- Props: mode, provider, apiKey, sourceLang, targetLang, styleSettings, etc.

#### LogsPanel.jsx

- Shows translation history and debug information
- Displays processed images for debugging
- Props: logs, debugImage, onClearLogs, onClose

#### RegionBox.jsx

- Allows users to adjust the OCR region in crop mode
- Provides drag and resize functionality
- Props: regionRect, onResizeStart, onSave, onCancel

#### TranslationOverlay.jsx

- Renders translated text overlays on screen
- Positions overlays based on OCR bounding boxes
- Props: translations, styleSettings, onMouseEnter

#### SelectionBox.jsx

- Shows the selection rectangle during brush mode
- Props: selectionRect

#### LoadingIndicator.jsx

- Displays processing status during OCR/translation
- Props: status

## Hooks (Business Logic Layer)

### useOCR.js

Encapsulates all Tesseract OCR logic:

- `recognizeText(image, language, onProgress)` - Runs OCR on image
- `extractTextBlocks(ocrResult)` - Extracts and groups text from OCR result
- `filterWords(words)` - Filters words by confidence and quality
- `groupWords(words)` - Groups nearby words into text blocks

**Usage:**

```jsx
const { recognizeText, extractTextBlocks } = useOCR();
const result = await recognizeText(image, lang, progressCallback);
const textBlocks = extractTextBlocks(result);
```

### useTranslation.js

Manages translation provider APIs:

- `translateMyMemory(text, source, target)` - Free translation service
- `translateDeepL(text, source, target, key)` - DeepL API translation

**Usage:**

```jsx
const { translateMyMemory, translateDeepL } = useTranslation();
const translated = await translateMyMemory('hello', 'eng', 'por');
```

### useImageProcessing.js

Handles image preprocessing for better OCR:

- `preprocessImage(dataUrl, rect)` - Crops, scales, and enhances image

**Usage:**

```jsx
const { preprocessImage } = useImageProcessing();
const processed = await preprocessImage(imageUrl, regionRect);
```

### useTextFiltering.js

Validates and filters OCR text:

- `isValidText(text, minLength)` - Checks if text is valid

**Usage:**

```jsx
const { isValidText } = useTextFiltering();
if (isValidText(detectedText)) {
  /* process */
}
```

## Utilities

### constants.js

Centralized configuration:

- `LANGUAGES` - Supported languages
- `PROVIDERS` - Translation providers
- `OCR_CONFIG` - OCR parameters (thresholds, scales)
- `DEFAULT_REGION` - Default crop region
- `DEFAULT_STYLE_SETTINGS` - Default UI appearance

### storage.js

LocalStorage wrapper functions:

- `loadState(key, defaultValue)` - Safely load from localStorage
- `saveState(key, value)` - Safely save to localStorage

## App.jsx (Main Component)

The App component now:

1. Initializes hooks for business logic
2. Manages application state (translations, UI visibility, settings)
3. Orchestrates data flow between hooks and components
4. Handles mouse interactions and region management
5. Renders components with appropriate props

Key functions:

- `processTranslation(rect)` - Main OCR and translation pipeline
- `triggerAction()` - Handles mode-specific translation initiation
- `handleMouseDown/Move/Up()` - Manages user interactions

## Data Flow

```
User Interaction (Mouse/Menu)
        ↓
App.jsx (State & Orchestration)
        ↓
Hooks (Business Logic)
        ├── useOCR → Tesseract processing
        ├── useTranslation → API calls
        ├── useImageProcessing → Image enhancement
        └── useTextFiltering → Text validation
        ↓
Components (UI Rendering)
        ├── FloatingMenu
        ├── SettingsPanel
        ├── LogsPanel
        ├── RegionBox
        └── TranslationOverlay
```

## Key Improvements

1. **Separation of Concerns**: Business logic is isolated in hooks, UI is in components
2. **Reusability**: Hooks can be used in other components without modification
3. **Testability**: Each hook and component can be tested independently
4. **Maintainability**: Changes to OCR logic don't affect UI components
5. **Scalability**: Easy to add new features without bloating App.jsx
6. **Code Organization**: Clear file structure makes navigation easier

## Configuration

All configurable values are in `utils/constants.js`:

```javascript
OCR_CONFIG = {
  CONFIDENCE_THRESHOLD: 40, // Minimum word confidence %
  MIN_WORD_LENGTH: 2, // Minimum characters
  MIN_WORD_SIZE: 8, // Minimum pixel size
  MIN_TEXT_LENGTH: 3, // Minimum block text length
  ASPECT_RATIO_MIN: 0.3, // Text width/height ratio limits
  ASPECT_RATIO_MAX: 4,
  UNIQUENESS_RATIO_MIN: 0.3, // Unique character ratio
  LINE_CONFIDENCE_THRESHOLD: 20, // Fallback line confidence
  IMAGE_SCALE: 3, // Upscaling factor for OCR
};
```

## Future Enhancements

1. Extract mouse interaction logic into a custom hook (`useMouseInteraction`)
2. Create a `useRegionManager` hook for region editing state
3. Add custom hooks for settings persistence
4. Create higher-order components for common patterns
5. Extract styling logic into CSS modules
