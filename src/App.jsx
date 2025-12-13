import React, { useState, useEffect, useRef } from 'react'
import Tesseract from 'tesseract.js'

// Language Options
const LANGUAGES = [
  { code: 'eng', label: 'English', tesseract: 'eng' },
  { code: 'por', label: 'Portuguese', tesseract: 'por' },
  { code: 'spa', label: 'Spanish', tesseract: 'spa' },
  { code: 'fra', label: 'French', tesseract: 'fra' },
  { code: 'deu', label: 'German', tesseract: 'deu' },
  { code: 'jpn', label: 'Japanese', tesseract: 'jpn' },
]

const PROVIDERS = [
  { id: 'mymemory', name: 'MyMemory (Free)', requiresKey: false },
  { id: 'deepl', name: 'DeepL API', requiresKey: true },
]

function App() {
  const [translations, setTranslations] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [status, setStatus] = useState('')

  // UI State
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showLogs, setShowLogs] = useState(false)

  // Logs State
  const [logs, setLogs] = useState([])
  const [debugImage, setDebugImage] = useState(null) // For debugging

  // --- STATE INITIALIZATION (Load from LocalStorage) ---
  const loadState = (key, def) => {
    const saved = localStorage.getItem(key)
    if (saved) return JSON.parse(saved)
    return def
  }

  // Settings
  const [sourceLang, setSourceLang] = useState(() => loadState('sourceLang', LANGUAGES[0]))
  const [targetLang, setTargetLang] = useState(() => loadState('targetLang', LANGUAGES[1]))
  const [mode, setMode] = useState(() => loadState('mode', 'crop'))

  // Provider Settings
  const [provider, setProvider] = useState(() => loadState('provider', PROVIDERS[0].id))
  // Load API Key from Env if available, otherwise localStorage, otherwise empty
  const [apiKey, setApiKey] = useState(() => {
    const saved = localStorage.getItem('apiKey')
    if (saved) return JSON.parse(saved)
    return import.meta.env.VITE_DEEPL_API_KEY || ''
  })

  // Appearance Settings
  const [styleSettings, setStyleSettings] = useState(() => loadState('styleSettings', {
    backgroundColor: '#ffffff',
    bgOpacity: 0.9,
    color: '#000000',
    fontSize: 14
  }))

  // Selection/Interaction State
  const [isInteracting, setIsInteracting] = useState(false)
  const [isWaitingForInput, setIsWaitingForInput] = useState(false)
  const [selectionStart, setSelectionStart] = useState(null)
  const [selectionRect, setSelectionRect] = useState(null)

  // Region State
  const [regionRect, setRegionRect] = useState(() => loadState('regionRect', { x: 100, y: 100, width: 300, height: 200 }))
  const [tempRegionRect, setTempRegionRect] = useState(null) // For cancelling edits
  const [isEditingRegion, setIsEditingRegion] = useState(false)
  const [isDraggingRegion, setIsDraggingRegion] = useState(false)
  const [isResizingRegion, setIsResizingRegion] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [resizeStart, setResizeStart] = useState(null)

  // --- PERSISTENCE EFFECTS ---
  useEffect(() => localStorage.setItem('sourceLang', JSON.stringify(sourceLang)), [sourceLang])
  useEffect(() => localStorage.setItem('targetLang', JSON.stringify(targetLang)), [targetLang])
  useEffect(() => localStorage.setItem('mode', JSON.stringify(mode)), [mode])
  useEffect(() => localStorage.setItem('provider', JSON.stringify(provider)), [provider])
  useEffect(() => localStorage.setItem('apiKey', JSON.stringify(apiKey)), [apiKey])
  useEffect(() => localStorage.setItem('styleSettings', JSON.stringify(styleSettings)), [styleSettings])
  useEffect(() => localStorage.setItem('regionRect', JSON.stringify(regionRect)), [regionRect])

  useEffect(() => {
    // Listen for global shortcut
    if (window.electron && window.electron.onTriggerTranslation) {
      window.electron.onTriggerTranslation(() => {
        triggerAction()
      })
    }

    // Listen for Escape key
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        clearAll()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mode, regionRect]) // Re-bind if mode/region changes

  // Manage Mouse Events / Window Click-through
  useEffect(() => {
    // If we are interacting, showing menu, settings, logs, or results, capture mouse.
    // Also if we are explicitly waiting for input (Brush active)
    // Also if we are editing the region
    const needsInteraction = isInteracting || isMenuOpen || showSettings || showLogs || translations.length > 0 || isProcessing || isWaitingForInput || isEditingRegion

    if (needsInteraction) {
      window.electron.setIgnoreMouseEvents(false)
    } else {
      window.electron.setIgnoreMouseEvents(true, { forward: true })
    }
  }, [isInteracting, isMenuOpen, showSettings, showLogs, translations.length, isProcessing, isWaitingForInput, isEditingRegion])

  // --- MOUSE HANDLERS ---

  const handleMouseDown = (e) => {
    // UI Interaction Check
    if (e.target.closest('.floating-menu-container') || e.target.closest('.settings-panel') || e.target.closest('.logs-panel') || e.target.closest('.translation-box') || e.target.closest('.region-handle') || e.target.closest('.region-controls') || e.target.closest('.adjust-region-btn')) {
      return
    }

    if (showSettings || isMenuOpen || showLogs) {
      setIsMenuOpen(false)
      setShowSettings(false)
      setShowLogs(false)
      return
    }

    // Region Dragging Logic
    if (isEditingRegion && e.target.closest('.region-box-border')) {
      setIsDraggingRegion(true)
      setDragOffset({
        x: e.clientX - regionRect.x,
        y: e.clientY - regionRect.y
      })
      return
    }

    // Region Resizing Logic (Handled by specific handles, but just in case)

    if (mode === 'global' || mode === 'crop') return

    // Brush (Quick Select) Logic
    if (mode === 'brush') {
      setIsInteracting(true)
      setSelectionStart({ x: e.clientX, y: e.clientY })
      setSelectionRect({ x: e.clientX, y: e.clientY, width: 0, height: 0 })
    }
  }

  const handleMouseMove = (e) => {
    if (isDraggingRegion) {
      setRegionRect(prev => ({
        ...prev,
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      }))
      return
    }

    if (isResizingRegion && resizeStart) {
      const deltaX = e.clientX - resizeStart.mouseX
      const deltaY = e.clientY - resizeStart.mouseY
      setRegionRect(prev => ({
        ...prev,
        width: Math.max(50, resizeStart.width + deltaX),
        height: Math.max(50, resizeStart.height + deltaY)
      }))
      return
    }

    if (!isInteracting) return

    if (mode === 'brush' && selectionStart) {
      const currentX = e.clientX
      const currentY = e.clientY

      const width = Math.abs(currentX - selectionStart.x)
      const height = Math.abs(currentY - selectionStart.y)
      const x = Math.min(currentX, selectionStart.x)
      const y = Math.min(currentY, selectionStart.y)

      setSelectionRect({ x, y, width, height })
    }
  }

  const handleMouseUp = async () => {
    setIsDraggingRegion(false)
    setIsResizingRegion(false)

    if (!isInteracting) return
    setIsInteracting(false)

    if (mode === 'brush' && selectionRect) {
      if (selectionRect.width > 10 && selectionRect.height > 10) {
        setIsWaitingForInput(false)
        await processTranslation(selectionRect)
      }
      setSelectionStart(null)
    }
  }

  // Region Resize Handlers
  const handleResizeStart = (e) => {
    e.stopPropagation()
    setIsResizingRegion(true)
    setResizeStart({
      mouseX: e.clientX,
      mouseY: e.clientY,
      width: regionRect.width,
      height: regionRect.height
    })
  }

  const startEditingRegion = () => {
    setTempRegionRect(regionRect)
    setIsEditingRegion(true)
    // Close settings to clear view
    setShowSettings(false)
  }

  const saveRegion = () => {
    setIsEditingRegion(false)
    setTempRegionRect(null)
  }

  const cancelRegion = () => {
    if (tempRegionRect) setRegionRect(tempRegionRect)
    setIsEditingRegion(false)
    setTempRegionRect(null)
  }

  // --- LOGIC ---

  const triggerAction = () => {
    if (mode === 'global') {
      handleGlobalTranslate()
    } else if (mode === 'crop') {
      // New Crop (Region) Mode
      // Just translate what is in the regionRect
      processTranslation(regionRect)
    } else {
      // Brush (Quick Select) Mode
      setTranslations([])
      setSelectionRect(null)
      setIsWaitingForInput(true) // Enable interaction for drawing
      setStatus(`Mode: BRUSH - Draw to Translate`)

      // Close menu to get it out of the way
      setIsMenuOpen(false)
      setShowSettings(false)
      setShowLogs(false)
    }
  }

  const handleGlobalTranslate = async () => {
    setIsMenuOpen(false)
    setIsWaitingForInput(false)
    const { width, height } = window.screen
    await processTranslation({ x: 0, y: 0, width, height })
  }

  const processTranslation = async (rect) => {
    if (isProcessing) return
    setIsProcessing(true)

    // HIDE UI BEFORE CAPTURE
    // We clear status and ensure overlays are hidden if needed
    setStatus('')

    // Small delay to allow React to render the hidden state and Electron to update
    await new Promise(r => setTimeout(r, 200))

    try {
      // 1. Capture Screen
      const imageDataUrl = await window.electron.captureScreen()

      // Now we can show status
      setStatus('Processing Image...')

      // 2. Preprocess Image (Crop, Scale, Binarize)
      const processedImage = await preprocessImage(imageDataUrl, rect)

      // For debugging: save the processed image
      setDebugImage(processedImage)

      // 3. Run OCR on Cropped Image
      setStatus(`Recognizing Text (${sourceLang.label})...`)
      const result = await Tesseract.recognize(
        processedImage,
        sourceLang.tesseract,
        {
          logger: m => {
            if (m.status === 'recognizing text') {
              setStatus(`OCR: ${Math.round(m.progress * 100)}%`)
            }
          }
        }
      )

      // Debug: Log full OCR result
      console.log('OCR Result:', result.data.text)
      console.log('Lines:', result.data.lines)

      setStatus('Translating...')

      const lines = result.data.lines.filter(line => line.confidence > 40 && line.text.trim().length > 1)
      const newTranslations = []

      for (const line of lines) {
        const text = line.text.trim()
        try {
          let translatedText = null

          if (provider === 'mymemory') {
            translatedText = await translateMyMemory(text, sourceLang.code, targetLang.code)
          } else if (provider === 'deepl') {
            translatedText = await translateDeepL(text, sourceLang.code, targetLang.code, apiKey)
          }

          if (translatedText) {
            const adjustedBbox = {
              x0: rect.x + line.bbox.x0,
              y0: rect.y + line.bbox.y0,
              x1: rect.x + line.bbox.x1,
              y1: rect.y + line.bbox.y1
            }

            newTranslations.push({
              text: translatedText,
              original: text,
              bbox: adjustedBbox
            })

            // Add to logs
            setLogs(prev => [{
              original: text,
              translated: translatedText,
              timestamp: new Date().toLocaleTimeString(),
              provider: provider
            }, ...prev])
          }
        } catch (err) {
          console.error(err)
          setStatus(`Error: ${err.message}`)
        }
      }

      if (newTranslations.length === 0) {
        setStatus('No text found.')
        setTimeout(() => setStatus(''), 2000)
      } else {
        setTranslations(newTranslations)
        setStatus('')
      }

    } catch (error) {
      console.error(error)
      setStatus('Error: ' + error.message)
    } finally {
      setIsProcessing(false)
    }
  }

  // --- TRANSLATION PROVIDERS ---

  const translateMyMemory = async (text, source, target) => {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${source}|${target}`
    const response = await fetch(url)
    const data = await response.json()
    return data.responseData ? data.responseData.translatedText : null
  }

  const translateDeepL = async (text, source, target, key) => {
    if (!key) throw new Error('DeepL API Key required')

    // DeepL uses 'EN' not 'ENG', 'PT' not 'POR' (usually PT-BR or PT-PT)
    // Simple mapping for demo
    const mapLang = (l) => {
      if (l === 'eng') return 'EN'
      if (l === 'por') return 'PT-BR' // Defaulting to PT-BR
      if (l === 'spa') return 'ES'
      if (l === 'fra') return 'FR'
      if (l === 'deu') return 'DE'
      if (l === 'jpn') return 'JA'
      return l.toUpperCase().slice(0, 2)
    }

    const targetCode = mapLang(target)
    const sourceCode = mapLang(source)

    // Determine free or pro endpoint
    const isFree = key.endsWith(':fx')
    const endpoint = isFree ? 'https://api-free.deepl.com/v2/translate' : 'https://api.deepl.com/v2/translate'

    const params = new URLSearchParams()
    params.append('text', text)
    params.append('target_lang', targetCode)
    params.append('source_lang', sourceCode)

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `DeepL-Auth-Key ${key}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.message || 'DeepL Error')
    }

    const data = await response.json()
    return data.translations && data.translations[0] ? data.translations[0].text : null
  }

  const preprocessImage = (dataUrl, rect) => {
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        // Scale up for better OCR
        const scale = 2
        const padding = 10

        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        canvas.width = (rect.width * scale) + (padding * 2)
        canvas.height = (rect.height * scale) + (padding * 2)

        // Fill white background
        ctx.fillStyle = '#FFFFFF'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        // Draw the cropped area scaled up
        ctx.drawImage(
          img,
          rect.x, rect.y, rect.width, rect.height,
          padding, padding, rect.width * scale, rect.height * scale
        )

        // Get image data for processing
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const data = imageData.data

        // Calculate average brightness to detect dark mode
        let totalBrightness = 0
        for (let i = 0; i < data.length; i += 4) {
          totalBrightness += (0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2])
        }
        const avgBrightness = totalBrightness / (data.length / 4)
        const isDarkBackground = avgBrightness < 128

        // Apply grayscale and optional inversion
        // DON'T do hard thresholding - it destroys text detail
        for (let i = 0; i < data.length; i += 4) {
          let gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]

          if (isDarkBackground) {
            gray = 255 - gray // Invert for dark backgrounds
          }

          // Just convert to grayscale without thresholding
          data[i] = gray
          data[i + 1] = gray
          data[i + 2] = gray
        }
        ctx.putImageData(imageData, 0, 0)

        resolve(canvas.toDataURL('image/png'))
      }
      img.src = dataUrl
    })
  }

  const clearAll = () => {
    setTranslations([])
    setSelectionRect(null)
    setIsWaitingForInput(false)
    setIsMenuOpen(false)
    setShowSettings(false)
    setShowLogs(false)
    setStatus('')
  }

  // Hover handlers to ensure we can click the floating menu
  const handleMouseEnterUI = () => window.electron.setIgnoreMouseEvents(false)
  const handleMouseLeaveUI = () => {
    if (!isInteracting && !isMenuOpen && !showSettings && !showLogs && translations.length === 0 && !isWaitingForInput && !isDraggingRegion && !isResizingRegion) {
      window.electron.setIgnoreMouseEvents(true, { forward: true })
    }
  }

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        position: 'relative',
        cursor: (mode === 'brush') && !isMenuOpen && !showSettings ? 'crosshair' : 'default'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >

      {/* Floating Menu Container */}
      <div
        className="floating-menu-container"
        onMouseEnter={handleMouseEnterUI}
        onMouseLeave={handleMouseLeaveUI}
      >
        {/* Main Toggle Button */}
        <button
          className={`main-toggle-btn ${isMenuOpen ? 'open' : ''}`}
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          title="Menu"
        >
          文
        </button>

        {/* Expanded Options */}
        {isMenuOpen && (
          <div className="menu-options">
            <button className="menu-btn" onClick={triggerAction} title="Translate (Ctrl+Z)">
              ▶
            </button>
            <button className="menu-btn" onClick={() => setShowSettings(!showSettings)} title="Settings">
              ⚙
            </button>
            <button className="menu-btn" onClick={() => setShowLogs(!showLogs)} title="Logs">
              📋
            </button>
            <button className="menu-btn close-btn" onClick={clearAll} title="Clear / Close">
              ✖
            </button>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div
          className="settings-panel"
          onMouseDown={e => e.stopPropagation()}
          onMouseEnter={handleMouseEnterUI}
        >
          <h3>Settings</h3>

          <div className="setting-group">
            <label>Mode:</label>
            <div className="mode-selector">
              <button className={mode === 'crop' ? 'active' : ''} onClick={() => setMode('crop')}>Region</button>
              <button className={mode === 'global' ? 'active' : ''} onClick={() => setMode('global')}>Global</button>
              <button className={mode === 'brush' ? 'active' : ''} onClick={() => setMode('brush')}>Brush</button>
            </div>
            {mode === 'crop' && (
              <button className="adjust-region-btn" onClick={startEditingRegion} style={{ marginTop: 10, width: '100%', padding: 5, cursor: 'pointer' }}>
                Adjust Region Area
              </button>
            )}
          </div>

          <div className="setting-group">
            <label>Translation Provider:</label>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>

          {provider === 'deepl' && (
            <div className="setting-group">
              <label>DeepL API Key:</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste your API Key here"
              />
              <small style={{ fontSize: 10, color: '#999' }}>Key usually ends with :fx for free tier</small>
            </div>
          )}

          <div className="setting-group">
            <label>Language:</label>
            <div style={{ display: 'flex', gap: 5 }}>
              <select value={sourceLang.code} onChange={(e) => setSourceLang(LANGUAGES.find(l => l.code === e.target.value))}>
                {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.code.toUpperCase()}</option>)}
              </select>
              <span>➡</span>
              <select value={targetLang.code} onChange={(e) => setTargetLang(LANGUAGES.find(l => l.code === e.target.value))}>
                {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.code.toUpperCase()}</option>)}
              </select>
            </div>
          </div>

          <div className="setting-group">
            <label>Background:</label>
            <div className="color-palette">
              {['#ffffff', '#000000', '#1a1a1a', '#fffae3', '#e3f2fd'].map(c => (
                <div
                  key={c}
                  className={`color-swatch ${styleSettings.backgroundColor === c ? 'active' : ''}`}
                  style={{ background: c, border: c === '#ffffff' ? '1px solid #ddd' : 'none' }}
                  onClick={() => setStyleSettings({ ...styleSettings, backgroundColor: c })}
                />
              ))}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 5 }}>
              <span style={{ fontSize: 10 }}>Opacity:</span>
              <input type="range" min="0.5" max="1" step="0.1" value={styleSettings.bgOpacity} onChange={e => setStyleSettings({ ...styleSettings, bgOpacity: parseFloat(e.target.value) })} />
            </div>
          </div>

          <div className="setting-group">
            <label>Text Color:</label>
            <div className="color-palette">
              {['#000000', '#ffffff', '#ffff00', '#00ff00', '#ff0000'].map(c => (
                <div
                  key={c}
                  className={`color-swatch ${styleSettings.color === c ? 'active' : ''}`}
                  style={{ background: c, border: c === '#ffffff' ? '1px solid #ddd' : 'none' }}
                  onClick={() => setStyleSettings({ ...styleSettings, color: c })}
                />
              ))}
            </div>
          </div>

          <div className="setting-group">
            <label>Font Size: {styleSettings.fontSize}px</label>
            <input type="range" min="10" max="30" value={styleSettings.fontSize} onChange={e => setStyleSettings({ ...styleSettings, fontSize: parseInt(e.target.value) })} />
          </div>

          <button onClick={() => setShowSettings(false)} style={{ marginTop: 10, width: '100%' }}>Close</button>
        </div>
      )}

      {/* Logs Panel */}
      {showLogs && (
        <div
          className="logs-panel"
          onMouseDown={e => e.stopPropagation()}
          onMouseEnter={handleMouseEnterUI}
        >
          <h3>Translation Logs</h3>
          <div className="logs-list">
            {logs.length === 0 ? (
              <p style={{ color: '#999', textAlign: 'center' }}>No logs yet.</p>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="log-item">
                  <div className="log-time">{log.timestamp} <span style={{ fontSize: 9, background: '#eee', padding: '1px 3px', borderRadius: 3 }}>{log.provider}</span></div>
                  <div className="log-original"><strong>Detected:</strong> {log.original}</div>
                  <div className="log-translated"><strong>Translated:</strong> {log.translated}</div>
                </div>
              ))
            )}
          </div>
          <button onClick={() => setLogs([])} style={{ marginTop: 10, width: '100%', background: '#ff4646', color: 'white', border: 'none', padding: 5, borderRadius: 4, cursor: 'pointer' }}>Clear Logs</button>

          {/* Debug Image */}
          {debugImage && (
            <div style={{ marginTop: 10 }}>
              <label style={{ fontSize: 11, color: '#999' }}>Last Captured Image (Debug):</label>
              <img src={debugImage} style={{ width: '100%', border: '1px solid #ddd', marginTop: 5 }} />
            </div>
          )}

          <button onClick={() => setShowLogs(false)} style={{ marginTop: 5, width: '100%' }}>Close</button>
        </div>
      )}

      {/* Region Box (For Crop Mode - Only when Editing) */}
      {mode === 'crop' && isEditingRegion && (
        <div
          className="region-box"
          style={{
            left: regionRect.x,
            top: regionRect.y,
            width: regionRect.width,
            height: regionRect.height
          }}
          onMouseEnter={handleMouseEnterUI}
          onMouseLeave={handleMouseLeaveUI}
        >
          <div className="region-box-border"></div>
          <div className="region-handle" onMouseDown={handleResizeStart}>↘</div>
          <div className="region-label">Adjust Region</div>
          <div className="region-controls">
            <button className="region-btn confirm" onClick={saveRegion} title="Save">✔</button>
            <button className="region-btn cancel" onClick={cancelRegion} title="Cancel">✖</button>
          </div>
        </div>
      )}

      {/* Visualizers */}
      {mode === 'brush' && selectionRect && (
        <div className="selection-box" style={{ left: selectionRect.x, top: selectionRect.y, width: selectionRect.width, height: selectionRect.height }} />
      )}

      {/* Loading */}
      {isProcessing && <div className="loading">{status}</div>}

      {/* Translations */}
      {translations.length > 0 && (
        <div className="overlay-container">
          {translations.map((item, index) => (
            <div
              key={index}
              className="translation-box"
              style={{
                left: item.bbox.x0,
                top: item.bbox.y0,
                width: item.bbox.x1 - item.bbox.x0,
                minHeight: item.bbox.y1 - item.bbox.y0,
                backgroundColor: styleSettings.backgroundColor, // Apply settings
                color: styleSettings.color,
                fontSize: `${styleSettings.fontSize}px`,
                opacity: styleSettings.bgOpacity
              }}
              title={item.original}
              onMouseEnter={handleMouseEnterUI}
            >
              {item.text}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App
