declare global {
  interface Window {
    twttr?: {
      widgets: {
        load: (el?: HTMLElement) => void;
      };
    };
  }
}

const WIDGETS_SRC = "https://platform.twitter.com/widgets.js";

export function loadTwitterWidgetsScript(): Promise<void> {
  if (window.twttr) return Promise.resolve();
  const existing = document.querySelector<HTMLScriptElement>(`script[src="${WIDGETS_SRC}"]`);
  if (existing) {
    return new Promise((resolve) => existing.addEventListener("load", () => resolve()));
  }
  return new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = WIDGETS_SRC;
    script.async = true;
    script.onload = () => resolve();
    document.body.appendChild(script);
  });
}
