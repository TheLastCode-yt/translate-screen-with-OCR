"use strict";
const { app, BrowserWindow, globalShortcut, ipcMain, desktopCapturer, screen } = require("electron");
const path = require("path");
process.env.DIST = path.join(__dirname, "../dist");
process.env.PUBLIC = app.isPackaged ? process.env.DIST : path.join(__dirname, "../public");
let win;
function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
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
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(process.env.DIST, "index.html"));
  }
  win.setIgnoreMouseEvents(true, { forward: true });
}
app.on("ready", () => {
  createWindow();
  const ret = globalShortcut.register("CommandOrControl+Z", () => {
    win.webContents.send("trigger-translation");
  });
  if (!ret) {
    console.log("registration failed");
  }
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
ipcMain.handle("capture-screen", async () => {
  const sources = await desktopCapturer.getSources({ types: ["screen"], thumbnailSize: screen.getPrimaryDisplay().size });
  const primarySource = sources[0];
  return primarySource.thumbnail.toDataURL();
});
ipcMain.on("set-ignore-mouse-events", (event, ignore, options) => {
  const win2 = BrowserWindow.fromWebContents(event.sender);
  win2.setIgnoreMouseEvents(ignore, options);
});
