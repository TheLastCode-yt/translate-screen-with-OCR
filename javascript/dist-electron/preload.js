"use strict";
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("electron", {
  onTriggerTranslation: (callback) => ipcRenderer.on("trigger-translation", callback),
  captureScreen: () => ipcRenderer.invoke("capture-screen"),
  setIgnoreMouseEvents: (ignore, options) => ipcRenderer.send("set-ignore-mouse-events", ignore, options)
});
