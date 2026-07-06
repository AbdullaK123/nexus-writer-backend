// eventBus.ts
export const paletteBus = new EventTarget();

export const triggerPaletteClose = () => {
  paletteBus.dispatchEvent(new Event("close"));
};
