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

  // Settings
  const [sourceLang, setSourceLang] = useState(LANGUAGES[0]) // English
  const [targetLang, setTargetLang] = useState(LANGUAGES[1]) // Portuguese
  const [mode, setMode] = useState('crop') // 'global', 'crop', 'brush'

  // Provider Settings
  const [provider, setProvider] = useState(PROVIDERS[0].id)
  const [apiKey, setApiKey] = useState('') // Store in state (in prod, use secure storage)

  // Appearance Settings
  const [styleSettings, setStyleSettings] = useState({
    backgroundColor: '#ffffff',
    bgOpacity: 0.9,
    color: '#000000',
    fontSize: 14
  })

  // Selection/Interaction State
  const [isInteracting, setIsInteracting] = useState(false) // Mouse down (drawing/cropping)
  const [isWaitingForInput, setIsWaitingForInput] = useState(false) // Active mode waiting for user action
  const [selectionStart, setSelectionStart] = useState(null)
  const [selectionRect, setSelectionRect] = useState(null) // For Crop

  // Brush State
  const canvasRef = useRef(null)
  const [brushPath, setBrushPath] = useState([])

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
  }, [mode]) // Re-bind if mode changes (triggerAction depends on mode)

  // Manage Mouse Events / Window Click-through
  useEffect(() => {
    // If we are interacting (drawing), showing menu, settings, logs, or results, capture mouse.
    // Also if we are explicitly waiting for input (Crop/Brush active)
    const needsInteraction = isInteracting || isMenuOpen || showSettings || showLogs || translations.length > 0 || isProcessing || isWaitingForInput

    // However, we want the floating button to ALWAYS be clickable. 
    // The standard Electron way for "click-through except elements" involves mouseover listeners on elements.
    // But since we have a full screen overlay for drawing, we manage it by state here.

    if (needsInteraction) {
      window.electron.setIgnoreMouseEvents(false)
    } else {
      window.electron.setIgnoreMouseEvents(true, { forward: true })
    }
  }, [isInteracting, isMenuOpen, showSettings, showLogs, translations.length, isProcessing, isWaitingForInput])

  // --- MOUSE HANDLERS (For Crop/Brush) ---

  const handleMouseDown = (e) => {
    // If clicking on UI, stop propagation (handled by UI elements)
    if (e.target.closest('.floating-menu-container') || e.target.closest('.settings-panel') || e.target.closest('.logs-panel') || e.target.closest('.translation-box') || e.target.closest('.brush-go-btn')) {
      return
    }

    if (showSettings || isMenuOpen || showLogs) {
      // If clicking outside settings/menu/logs, close them?
      setIsMenuOpen(false)
      setShowSettings(false)
      setShowLogs(false)
      return
    }

    if (mode === 'global') return

    setIsInteracting(true)

    if (mode === 'crop') {
      setSelectionStart({ x: e.clientX, y: e.clientY })
      setSelectionRect({ x: e.clientX, y: e.clientY, width: 0, height: 0 })
    } else if (mode === 'brush') {
      setBrushPath([{ x: e.clientX, y: e.clientY }])
    }
  }

  const handleMouseMove = (e) => {
    if (!isInteracting) return

    if (mode === 'crop' && selectionStart) {
      const currentX = e.clientX
      const currentY = e.clientY

      const width = Math.abs(currentX - selectionStart.x)
      const height = Math.abs(currentY - selectionStart.y)
      const x = Math.min(currentX, selectionStart.x)
      const y = Math.min(currentY, selectionStart.y)

      setSelectionRect({ x, y, width, height })
    } else if (mode === 'brush') {
      setBrushPath(prev => [...prev, { x: e.clientX, y: e.clientY }])
    }
  }

  const handleMouseUp = async () => {
    if (!isInteracting) return
    setIsInteracting(false)

    if (mode === 'crop' && selectionRect) {
      if (selectionRect.width > 10 && selectionRect.height > 10) {
        setIsWaitingForInput(false) // Stop waiting, start processing
        await processTranslation(selectionRect)
      }
      setSelectionStart(null)
    }
  }

  // --- LOGIC ---

  const triggerAction = () => {
    if (mode === 'global') {
      handleGlobalTranslate()
    } else {
      // For Crop/Brush, we just ensure we are ready to draw.
      // Clearing previous results
      setTranslations([])
      setBrushPath([])
      setSelectionRect(null)
      setIsWaitingForInput(true) // Enable interaction for drawing
      setStatus(`Mode: ${mode.toUpperCase()} - Draw to Translate`)

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

  const handleBrushTranslate = async () => {
    if (brushPath.length === 0) return

    let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0
    brushPath.forEach(p => {
      if (p.x < minX) minX = p.x
      if (p.y < minY) minY = p.y
      if (p.x > maxX) maxX = p.x
      if (p.y > maxY) maxY = p.y
    })

    const padding = 20
    const rect = {
      x: Math.max(0, minX - padding),
      y: Math.max(0, minY - padding),
      width: (maxX - minX) + (padding * 2),
      height: (maxY - minY) + (padding * 2)
    }

    await processTranslation(rect, true)
  }

  const processTranslation = async (rect, useMask = false) => {
    if (isProcessing) return
    setIsProcessing(true)
    setStatus('Capturing Screen...')
    setTranslations([])

    try {
      // 1. Capture Screen
      const imageDataUrl = await window.electron.captureScreen()

      // 2. Preprocess Image (Crop, Scale, Binarize)
      setStatus('Processing Image...')
      const processedImage = await preprocessImage(imageDataUrl, rect, useMask)

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
          },
          tessedit_pageseg_mode: '6', // PSM 6: Assume a single uniform block of text
        }
      )

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
      if (mode === 'crop') setSelectionRect(null)
      if (mode === 'brush') setBrushPath([])
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

  const preprocessImage = (dataUrl, rect, useMask) => {
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        const scale = 2.5 // Upscale to improve OCR on small text
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        canvas.width = rect.width * scale
        canvas.height = rect.height * scale

        // Draw the cropped area scaled up
        ctx.drawImage(img, rect.x, rect.y, rect.width, rect.height, 0, 0, canvas.width, canvas.height)

        // If Brush mode, we mask out everything NOT in the brush path
        if (useMask && brushPath.length > 0) {
          ctx.globalCompositeOperation = 'destination-in'
          ctx.beginPath()
          ctx.lineCap = 'round'
          ctx.lineJoin = 'round'
          ctx.lineWidth = 30 * scale // Scale brush size too

          brushPath.forEach((p, i) => {
            const lx = (p.x - rect.x) * scale
            const ly = (p.y - rect.y) * scale
            if (i === 0) ctx.moveTo(lx, ly)
            else ctx.lineTo(lx, ly)
          })
          ctx.stroke()

          ctx.globalCompositeOperation = 'source-over'

          // Fill transparent with white (Tesseract prefers white background)
          const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height)
          const data = imgData.data
          for (let i = 0; i < data.length; i += 4) {
            if (data[i + 3] === 0) {
              data[i] = 255; data[i + 1] = 255; data[i + 2] = 255; data[i + 3] = 255;
            }
          }
          ctx.putImageData(imgData, 0, 0)
        }

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const data = imageData.data

        // 1. Calculate Average Brightness to detect dark mode
        let totalBrightness = 0
        for (let i = 0; i < data.length; i += 4) {
          totalBrightness += (data[i] + data[i + 1] + data[i + 2]) / 3
        }
        const avgBrightness = totalBrightness / (data.length / 4)
        const isDarkBackground = avgBrightness < 128

        // 2. Grayscale, Invert (if needed), and Binarize
        for (let i = 0; i < data.length; i += 4) {
          let avg = (data[i] + data[i + 1] + data[i + 2]) / 3

          if (isDarkBackground) {
            // Invert colors to get Black Text on White Background
            avg = 255 - avg
          }

          // Increase contrast / Thresholding
          // Using a slightly higher threshold to clean up noise
          const color = avg > 150 ? 255 : 0

          data[i] = color; data[i + 1] = color; data[i + 2] = color
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
    setBrushPath([])
    setIsWaitingForInput(false)
    setIsMenuOpen(false)
    setShowSettings(false)
    setShowLogs(false)
    setStatus('')
  }

  // Hover handlers to ensure we can click the floating menu
  const handleMouseEnterUI = () => window.electron.setIgnoreMouseEvents(false)
  const handleMouseLeaveUI = () => {
    if (!isInteracting && !isMenuOpen && !showSettings && !showLogs && translations.length === 0 && !isWaitingForInput) {
      window.electron.setIgnoreMouseEvents(true, { forward: true })
    }
  }

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        position: 'relative',
        cursor: (mode === 'crop' || mode === 'brush') && !isMenuOpen && !showSettings ? (mode === 'crop' ? 'crosshair' : 'cell') : 'default'
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

      {/* Brush "GO" Button */}
      {mode === 'brush' && brushPath.length > 0 && (
        <button
          className="brush-go-btn"
          style={{
            position: 'absolute',
            left: brushPath[brushPath.length - 1].x + 20,
            top: brushPath[brushPath.length - 1].y
          }}
          onClick={(e) => { e.stopPropagation(); handleBrushTranslate(); }}
          onMouseEnter={handleMouseEnterUI}
        >
          GO
        </button>
      )}

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
              <button className={mode === 'crop' ? 'active' : ''} onClick={() => setMode('crop')}>Crop</button>
              <button className={mode === 'global' ? 'active' : ''} onClick={() => setMode('global')}>Global</button>
              <button className={mode === 'brush' ? 'active' : ''} onClick={() => setMode('brush')}>Brush</button>
            </div>
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
            <label>Background Color:</label>
            <input type="color" value={styleSettings.backgroundColor} onChange={e => setStyleSettings({ ...styleSettings, backgroundColor: e.target.value })} />
          </div>

          <div className="setting-group">
            <label>Text Color:</label>
            <input type="color" value={styleSettings.color} onChange={e => setStyleSettings({ ...styleSettings, color: e.target.value })} />
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
          <button onClick={() => setShowLogs(false)} style={{ marginTop: 5, width: '100%' }}>Close</button>
        </div>
      )}

      {/* Visualizers */}
      {mode === 'crop' && selectionRect && (
        <div className="selection-box" style={{ left: selectionRect.x, top: selectionRect.y, width: selectionRect.width, height: selectionRect.height }} />
      )}

      {mode === 'brush' && (
        <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <polyline
            points={brushPath.map(p => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke="rgba(255, 70, 70, 0.5)"
            strokeWidth="30"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
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
