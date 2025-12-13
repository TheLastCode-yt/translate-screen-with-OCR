const { app, BrowserWindow, globalShortcut, ipcMain, desktopCapturer, screen } = require('electron')
const path = require('path')

process.env.DIST = path.join(__dirname, '../dist')
process.env.PUBLIC = app.isPackaged ? process.env.DIST : path.join(__dirname, '../public')

let win

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  win = new BrowserWindow({
    width,
    height,
    x: 0,
    y: 0,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  // Load the index.html of the app.
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }

  // Make window click-through initially (except for the UI elements we want to interact with)
  // We will handle this dynamically from the renderer
  win.setIgnoreMouseEvents(true, { forward: true })

  // Open DevTools for debugging (optional, remove in prod)
  // win.webContents.openDevTools({ mode: 'detach' })
}

app.on('ready', () => {
  createWindow()

  // Register a 'CommandOrControl+Z' shortcut listener.
  const ret = globalShortcut.register('CommandOrControl+Z', () => {
    win.webContents.send('trigger-translation')
  })

  if (!ret) {
    console.log('registration failed')
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC Handlers
ipcMain.handle('capture-screen', async () => {
  // Get the display where the app window is located
  const windowBounds = win.getBounds()
  const displays = screen.getAllDisplays()

  // Find which display the window is on
  let targetDisplay = screen.getPrimaryDisplay()
  for (const display of displays) {
    const { x, y, width, height } = display.bounds
    if (windowBounds.x >= x && windowBounds.x < x + width &&
      windowBounds.y >= y && windowBounds.y < y + height) {
      targetDisplay = display
      break
    }
  }

  // Get high quality screenshot
  const { width, height } = targetDisplay.size
  const scaleFactor = targetDisplay.scaleFactor || 1

  const sources = await desktopCapturer.getSources({
    types: ['screen'],
    thumbnailSize: {
      width: Math.floor(width * scaleFactor),
      height: Math.floor(height * scaleFactor)
    }
  })

  // Find the source for our target display
  // desktopCapturer returns sources with display_id matching screen.id
  let targetSource = sources[0]
  for (const source of sources) {
    if (source.display_id === String(targetDisplay.id)) {
      targetSource = source
      break
    }
  }

  return targetSource.thumbnail.toDataURL()
})

ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  win.setIgnoreMouseEvents(ignore, options)
})
