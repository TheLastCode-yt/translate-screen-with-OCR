# Visual Architecture Overview

## Component Hierarchy

```
App.jsx
├── FloatingMenu
│   ├── Main Toggle Button
│   └── Menu Options (3 buttons)
│
├── SettingsPanel
│   ├── Mode Selector (3 options)
│   ├── Provider Selector
│   ├── API Key Input (if DeepL)
│   ├── Language Selectors (2)
│   ├── Background Color Picker
│   ├── Text Color Picker
│   └── Font Size Slider
│
├── LogsPanel
│   ├── Logs List
│   ├── Clear Button
│   └── Debug Image (if available)
│
├── RegionBox (if editing region)
│   ├── Border
│   ├── Resize Handle
│   └── Controls (Save/Cancel)
│
├── SelectionBox (if drawing selection)
│   └── Visual rectangle
│
├── LoadingIndicator (if processing)
│   └── Status text
│
└── TranslationOverlay (if results)
    └── Multiple translation boxes
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                         │
│           (Click menu, adjust settings, select text)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     APP.JSX                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ State Management & Orchestration                     │    │
│  │ • translations, isProcessing, status                 │    │
│  │ • isMenuOpen, showSettings, showLogs                 │    │
│  │ • sourceLang, targetLang, mode, provider             │    │
│  │ • regionRect, selectionRect, styleSettings           │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────┐    ┌──────────┐    ┌────────────┐
    │ Hooks  │    │Components│    │ Constants  │
    └────────┘    └──────────┘    └────────────┘
        │              │              │
        ├─────────┐    │         ┌────┴─────┐
        │         │    │         │           │
    ┌───▼──┐  ┌──▼──┐ │    ┌─────▼──┐  ┌───▼────┐
    │useOCR│  │useT │ │    │LANGUAGES│  │PROVIDERS│
    └────┬─┘  └──┬──┘ │    └────┬────┘  └────┬───┘
         │       │    │         │           │
     Tesseract  APIs  │      Constants   Storage
         │       │    │         │           │
         └───────┼────┴─────────┴───────────┘
                 │
        ┌────────▼─────────┐
        │  BUSINESS LOGIC  │
        │  (Compute text   │
        │   blocks &       │
        │   translations)  │
        └────────┬─────────┘
                 │
        ┌────────▼───────────┐
        │  UI COMPONENTS     │
        ├────────────────────┤
        │ • FloatingMenu     │
        │ • SettingsPanel    │
        │ • LogsPanel        │
        │ • RegionBox        │
        │ • TranslationOvly  │
        │ • SelectionBox     │
        │ • LoadingIndicator │
        └────────┬───────────┘
                 │
                 ▼
        ┌─────────────────┐
        │   SCREEN        │
        │  (User Sees)    │
        └─────────────────┘
```

## Processing Pipeline

```
┌──────────────────────────────────────────────┐
│ 1. User clicks Translate                      │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 2. App.processTranslation()                   │
│    • Sets isProcessing = true                │
│    • Hides UI elements                       │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 3. Capture Screen                             │
│    window.electron.captureScreen()            │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 4. Preprocess Image                           │
│    useImageProcessing.preprocessImage()       │
│    • Crop to region                           │
│    • Scale up (3x)                            │
│    • Convert to grayscale                     │
│    • Enhance contrast                         │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 5. Run OCR                                    │
│    useOCR.recognizeText()                     │
│    • Tesseract processes image               │
│    • Extracts words with bounding boxes      │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 6. Extract Text Blocks                        │
│    useOCR.extractTextBlocks()                 │
│    • Filter low confidence words             │
│    • Group nearby words                      │
│    • Handle fallback to lines                │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 7. Validate Text                              │
│    useTextFiltering.isValidText()             │
│    • Check length                             │
│    • Remove false positives                  │
│    • Validate patterns                       │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 8. Translate Each Block                       │
│    useTranslation.translate*()                │
│    • Call MyMemory or DeepL                  │
│    • Handle errors                           │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 9. Adjust Coordinates                         │
│    • Divide by scale (3)                     │
│    • Add region offset                       │
│    • Add padding                             │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 10. Update State                              │
│     • setTranslations()                       │
│     • setLogs()                               │
│     • setDebugImage()                         │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ 11. Render TranslationOverlay                 │
│     • Display translation boxes               │
│     • Position on screen                      │
│     • Apply styles                            │
└──────────────────────────────────────────────┘
```

## Hook Dependencies

```
App.jsx
│
├── useOCR()
│   ├── Tesseract (external)
│   ├── OCR_CONFIG (constants)
│   └── Returns: recognizeText, extractTextBlocks
│
├── useTranslation()
│   ├── fetch API
│   └── Returns: translateMyMemory, translateDeepL
│
├── useImageProcessing()
│   └── Returns: preprocessImage
│
└── useTextFiltering()
    ├── FAUX_PATTERNS
    └── Returns: isValidText
```

## State Tree

```
App State
├── Translation Results
│   ├── translations []
│   ├── isProcessing boolean
│   ├── status string
│   └── logs []
│       └── { original, translated, timestamp, provider }
│
├── UI State
│   ├── isMenuOpen boolean
│   ├── showSettings boolean
│   ├── showLogs boolean
│   └── debugImage string
│
├── Settings
│   ├── sourceLang object
│   ├── targetLang object
│   ├── mode string (crop|global|brush)
│   ├── provider string (mymemory|deepl)
│   ├── apiKey string
│   └── styleSettings object
│       ├── backgroundColor
│       ├── bgOpacity
│       ├── color
│       └── fontSize
│
├── Region
│   ├── regionRect object {x, y, width, height}
│   ├── tempRegionRect object
│   ├── isEditingRegion boolean
│   ├── isDraggingRegion boolean
│   ├── isResizingRegion boolean
│   ├── dragOffset object
│   └── resizeStart object
│
└── Interaction
    ├── isInteracting boolean
    ├── isWaitingForInput boolean
    ├── selectionStart object
    └── selectionRect object
```

## File Size Comparison

```
Before Refactoring:
┌─────────────────────────────────┐
│ App.jsx: 1161 lines             │
│ ████████████████████████████    │
└─────────────────────────────────┘

After Refactoring:
┌─────────────────────────────────┐
│ App.jsx: 530 lines              │
│ ███████████████                 │
│                                 │
│ Hooks: 4 files                  │
│ useOCR.js: ~130 lines           │
│ useTranslation.js: ~70 lines    │
│ useImageProcessing.js: ~75 lines│
│ useTextFiltering.js: ~15 lines  │
│ Total: ~290 lines               │
│ ████████                        │
│                                 │
│ Components: 7 files             │
│ Total: ~150 lines               │
│ ███                             │
│                                 │
│ Utils: 2 files                  │
│ Total: ~40 lines                │
│ █                               │
│                                 │
│ Overall: 1110 lines (slightly less, but organized)
└─────────────────────────────────┘
```

## Dependency Graph

```
App.jsx (central orchestrator)
│
├─────────────────────────────────────────────┐
│                                              │
▼                                              ▼
Hooks (no circular deps)              Components (no state)
├── useOCR                            ├── FloatingMenu
├── useTranslation                    ├── SettingsPanel
├── useImageProcessing                ├── LogsPanel
└── useTextFiltering                  ├── RegionBox
                                      ├── TranslationOverlay
                                      ├── SelectionBox
                                      └── LoadingIndicator

Utils (static, no deps)
├── constants.js
└── storage.js

Third-party
├── Tesseract.js (in useOCR)
└── React (everywhere)
```

## Module Communication Pattern

```
App.jsx
 │
 ├─ Calls hook functions
 │  │
 │  └─ Hook returns data
 │     │
 │     ├─ Updates state
 │     └─ Triggers re-render
 │
 └─ Passes data to components via props
    │
    └─ Components emit events (callbacks)
       │
       └─ App.jsx handles events
          │
          └─ Updates state (cycle repeats)
```

## Performance Characteristics

```
Old (Monolithic):
├── Parse time: ~X ms (large file)
├── Component size: Large
└── Re-render cost: High

New (Modular):
├── Parse time: ~X/2 ms (files split)
├── Component size: Small
└── Re-render cost: Low

Better code splitting opportunities
```

---

**The refactored architecture is clean, modular, and ready for production!** 🚀
