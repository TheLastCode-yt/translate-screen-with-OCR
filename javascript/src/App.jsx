import React, { useState, useEffect } from 'react';
import {
  LANGUAGES,
  PROVIDERS,
  OCR_CONFIG,
  DEFAULT_REGION,
  DEFAULT_STYLE_SETTINGS,
} from './utils/constants';
import { loadState, saveState } from './utils/storage';
import { useImageProcessing } from './hooks/useImageProcessing';
import { useTranslation } from './hooks/useTranslation';
import { useOCR } from './hooks/useOCR';
import { useTextFiltering } from './hooks/useTextFiltering';
import FloatingMenu from './components/FloatingMenu';
import SettingsPanel from './components/SettingsPanel';
import LogsPanel from './components/LogsPanel';
import RegionBox from './components/RegionBox';
import TranslationOverlay from './components/TranslationOverlay';
import SelectionBox from './components/SelectionBox';
import LoadingIndicator from './components/LoadingIndicator';

function App() {
  // Initialize hooks
  const { preprocessImage } = useImageProcessing();
  const { translateMyMemory, translateDeepL } = useTranslation();
  const { recognizeText, extractTextBlocks } = useOCR();
  const { isValidText } = useTextFiltering();

  // Translation State
  const [translations, setTranslations] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');

  // UI State
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  // Logs State
  const [logs, setLogs] = useState([]);
  const [debugImage, setDebugImage] = useState(null);

  // Settings
  const [sourceLang, setSourceLang] = useState(() =>
    loadState('sourceLang', LANGUAGES[0])
  );
  const [targetLang, setTargetLang] = useState(() =>
    loadState('targetLang', LANGUAGES[1])
  );
  const [mode, setMode] = useState(() => loadState('mode', 'crop'));

  // Provider Settings
  const [provider, setProvider] = useState(() =>
    loadState('provider', PROVIDERS[0].id)
  );
  const [apiKey, setApiKey] = useState(() => {
    const saved = localStorage.getItem('apiKey');
    if (saved) return JSON.parse(saved);
    return import.meta.env.VITE_DEEPL_API_KEY || '';
  });

  // Appearance Settings
  const [styleSettings, setStyleSettings] = useState(() =>
    loadState('styleSettings', DEFAULT_STYLE_SETTINGS)
  );

  // Region State
  const [regionRect, setRegionRect] = useState(() =>
    loadState('regionRect', DEFAULT_REGION)
  );
  const [tempRegionRect, setTempRegionRect] = useState(null);
  const [isEditingRegion, setIsEditingRegion] = useState(false);
  const [isDraggingRegion, setIsDraggingRegion] = useState(false);
  const [isResizingRegion, setIsResizingRegion] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [resizeStart, setResizeStart] = useState(null);

  // Selection/Interaction State
  const [isInteracting, setIsInteracting] = useState(false);
  const [isWaitingForInput, setIsWaitingForInput] = useState(false);
  const [selectionStart, setSelectionStart] = useState(null);
  const [selectionRect, setSelectionRect] = useState(null);

  // --- PERSISTENCE EFFECTS ---
  useEffect(() => saveState('sourceLang', sourceLang), [sourceLang]);
  useEffect(() => saveState('targetLang', targetLang), [targetLang]);
  useEffect(() => saveState('mode', mode), [mode]);
  useEffect(() => saveState('provider', provider), [provider]);
  useEffect(() => saveState('apiKey', apiKey), [apiKey]);
  useEffect(() => saveState('styleSettings', styleSettings), [styleSettings]);
  useEffect(() => saveState('regionRect', regionRect), [regionRect]);

  useEffect(() => {
    // Listen for global shortcut
    if (window.electron && window.electron.onTriggerTranslation) {
      window.electron.onTriggerTranslation(() => {
        triggerAction();
      });
    }

    // Listen for Escape key
    const handleKeyDown = e => {
      if (e.key === 'Escape') {
        clearAll();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mode, regionRect]); // Re-bind if mode/region changes

  // Manage Mouse Events / Window Click-through
  useEffect(() => {
    // If we are interacting, showing menu, settings, logs, or results, capture mouse.
    // Also if we are explicitly waiting for input (Brush active)
    // Also if we are editing the region
    const needsInteraction =
      isInteracting ||
      isMenuOpen ||
      showSettings ||
      showLogs ||
      translations.length > 0 ||
      isProcessing ||
      isWaitingForInput ||
      isEditingRegion;

    if (needsInteraction) {
      window.electron.setIgnoreMouseEvents(false);
    } else {
      window.electron.setIgnoreMouseEvents(true, { forward: true });
    }
  }, [
    isInteracting,
    isMenuOpen,
    showSettings,
    showLogs,
    translations.length,
    isProcessing,
    isWaitingForInput,
    isEditingRegion,
  ]);

  // --- MOUSE HANDLERS ---

  const handleMouseDown = e => {
    // UI Interaction Check
    if (
      e.target.closest('.floating-menu-container') ||
      e.target.closest('.settings-panel') ||
      e.target.closest('.logs-panel') ||
      e.target.closest('.translation-box') ||
      e.target.closest('.region-handle') ||
      e.target.closest('.region-controls') ||
      e.target.closest('.adjust-region-btn')
    ) {
      return;
    }

    if (showSettings || isMenuOpen || showLogs) {
      setIsMenuOpen(false);
      setShowSettings(false);
      setShowLogs(false);
      return;
    }

    // Region Dragging Logic
    if (isEditingRegion && e.target.closest('.region-box-border')) {
      setIsDraggingRegion(true);
      setDragOffset({
        x: e.clientX - regionRect.x,
        y: e.clientY - regionRect.y,
      });
      return;
    }

    // Region Resizing Logic (Handled by specific handles, but just in case)

    if (mode === 'global' || mode === 'crop') return;

    // Brush (Quick Select) Logic
    if (mode === 'brush') {
      setIsInteracting(true);
      setSelectionStart({ x: e.clientX, y: e.clientY });
      setSelectionRect({ x: e.clientX, y: e.clientY, width: 0, height: 0 });
    }
  };

  const handleMouseMove = e => {
    if (isDraggingRegion) {
      setRegionRect(prev => ({
        ...prev,
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y,
      }));
      return;
    }

    if (isResizingRegion && resizeStart) {
      const deltaX = e.clientX - resizeStart.mouseX;
      const deltaY = e.clientY - resizeStart.mouseY;
      setRegionRect(prev => ({
        ...prev,
        width: Math.max(50, resizeStart.width + deltaX),
        height: Math.max(50, resizeStart.height + deltaY),
      }));
      return;
    }

    if (!isInteracting) return;

    if (mode === 'brush' && selectionStart) {
      const currentX = e.clientX;
      const currentY = e.clientY;

      const width = Math.abs(currentX - selectionStart.x);
      const height = Math.abs(currentY - selectionStart.y);
      const x = Math.min(currentX, selectionStart.x);
      const y = Math.min(currentY, selectionStart.y);

      setSelectionRect({ x, y, width, height });
    }
  };

  const handleMouseUp = async () => {
    setIsDraggingRegion(false);
    setIsResizingRegion(false);

    if (!isInteracting) return;
    setIsInteracting(false);

    if (mode === 'brush' && selectionRect) {
      if (selectionRect.width > 10 && selectionRect.height > 10) {
        setIsWaitingForInput(false);
        await processTranslation(selectionRect);
      }
      setSelectionStart(null);
    }
  };

  // Region Resize Handlers
  const handleResizeStart = e => {
    e.stopPropagation();
    setIsResizingRegion(true);
    setResizeStart({
      mouseX: e.clientX,
      mouseY: e.clientY,
      width: regionRect.width,
      height: regionRect.height,
    });
  };

  const startEditingRegion = () => {
    setTempRegionRect(regionRect);
    setIsEditingRegion(true);
    // Close settings to clear view
    setShowSettings(false);
  };

  const saveRegion = () => {
    setIsEditingRegion(false);
    setTempRegionRect(null);
  };

  const cancelRegion = () => {
    if (tempRegionRect) setRegionRect(tempRegionRect);
    setIsEditingRegion(false);
    setTempRegionRect(null);
  };

  // --- LOGIC ---

  const triggerAction = () => {
    if (mode === 'global') {
      handleGlobalTranslate();
    } else if (mode === 'crop') {
      // New Crop (Region) Mode
      // Just translate what is in the regionRect
      processTranslation(regionRect);
    } else {
      // Brush (Quick Select) Mode
      setTranslations([]);
      setSelectionRect(null);
      setIsWaitingForInput(true); // Enable interaction for drawing
      setStatus(`Mode: BRUSH - Draw to Translate`);

      // Close menu to get it out of the way
      setIsMenuOpen(false);
      setShowSettings(false);
      setShowLogs(false);
    }
  };

  const handleGlobalTranslate = async () => {
    setIsMenuOpen(false);
    setIsWaitingForInput(false);
    const { width, height } = window.screen;
    await processTranslation({ x: 0, y: 0, width, height });
  };

  const processTranslation = async rect => {
    if (isProcessing) return;
    setIsProcessing(true);

    setStatus('');
    await new Promise(r => setTimeout(r, 200));

    try {
      // 1. Capture Screen
      const imageDataUrl = await window.electron.captureScreen();
      setStatus('Processing Image...');

      // 2. Preprocess Image
      const processedImage = await preprocessImage(imageDataUrl, rect);
      setDebugImage(processedImage);

      // 3. Run OCR
      setStatus(`Recognizing Text (${sourceLang.label})...`);
      const result = await recognizeText(
        processedImage,
        sourceLang.tesseract,
        progress => setStatus(`OCR: ${progress}%`)
      );

      setStatus('Translating...');

      // Extract text blocks from OCR result
      const textBlocks = extractTextBlocks(result);
      const newTranslations = [];

      // Process each text block
      for (const block of textBlocks) {
        let text = '';
        if (block.words && block.words.length > 0) {
          text = block.words
            .map(w => w.text.trim())
            .join(' ')
            .trim();
        } else if (block.text) {
          text = block.text;
        }

        // Filter invalid text
        if (!isValidText(text)) continue;

        try {
          let translatedText = null;

          if (provider === 'mymemory') {
            translatedText = await translateMyMemory(
              text,
              sourceLang.code,
              targetLang.code
            );
          } else if (provider === 'deepl') {
            translatedText = await translateDeepL(
              text,
              sourceLang.code,
              targetLang.code,
              apiKey
            );
          }

          if (translatedText) {
            const padding = 2;
            const adjustedBbox = {
              x0: Math.max(
                0,
                rect.x + block.bbox.x0 / OCR_CONFIG.IMAGE_SCALE - padding
              ),
              y0: Math.max(
                0,
                rect.y + block.bbox.y0 / OCR_CONFIG.IMAGE_SCALE - padding
              ),
              x1: rect.x + block.bbox.x1 / OCR_CONFIG.IMAGE_SCALE + padding,
              y1: rect.y + block.bbox.y1 / OCR_CONFIG.IMAGE_SCALE + padding,
            };

            console.log(
              `Translation: "${text}" -> "${translatedText}" at bbox:`,
              adjustedBbox
            );

            newTranslations.push({
              text: translatedText,
              original: text,
              bbox: adjustedBbox,
            });

            setLogs(prev => [
              {
                original: text,
                translated: translatedText,
                timestamp: new Date().toLocaleTimeString(),
                provider: provider,
              },
              ...prev,
            ]);
          }
        } catch (err) {
          console.error(err);
          setStatus(`Error: ${err.message}`);
        }
      }

      if (newTranslations.length === 0) {
        setStatus('No text found.');
        setTimeout(() => setStatus(''), 2000);
      } else {
        setTranslations(newTranslations);
        setStatus('');
      }
    } catch (error) {
      console.error(error);
      setStatus('Error: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const clearAll = () => {
    setTranslations([]);
    setSelectionRect(null);
    setIsWaitingForInput(false);
    setIsMenuOpen(false);
    setShowSettings(false);
    setShowLogs(false);
    setStatus('');
  };

  const handleMouseEnterUI = () => window.electron.setIgnoreMouseEvents(false);
  const handleMouseLeaveUI = () => {
    if (
      !isInteracting &&
      !isMenuOpen &&
      !showSettings &&
      !showLogs &&
      translations.length === 0 &&
      !isWaitingForInput &&
      !isDraggingRegion &&
      !isResizingRegion
    ) {
      window.electron.setIgnoreMouseEvents(true, { forward: true });
    }
  };

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        position: 'relative',
        cursor:
          mode === 'brush' && !isMenuOpen && !showSettings
            ? 'crosshair'
            : 'default',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
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

      {showSettings && (
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
      )}

      {showLogs && (
        <LogsPanel
          logs={logs}
          debugImage={debugImage}
          onClearLogs={() => setLogs([])}
          onClose={() => setShowLogs(false)}
          onMouseEnter={handleMouseEnterUI}
        />
      )}

      {mode === 'crop' && isEditingRegion && (
        <RegionBox
          regionRect={regionRect}
          onResizeStart={handleResizeStart}
          onSave={saveRegion}
          onCancel={cancelRegion}
          onMouseEnter={handleMouseEnterUI}
          onMouseLeave={handleMouseLeaveUI}
        />
      )}

      {mode === 'brush' && selectionRect && (
        <SelectionBox selectionRect={selectionRect} />
      )}

      {isProcessing && <LoadingIndicator status={status} />}

      {translations.length > 0 && (
        <TranslationOverlay
          translations={translations}
          styleSettings={styleSettings}
          onMouseEnter={handleMouseEnterUI}
        />
      )}
    </div>
  );
}

export default App;
