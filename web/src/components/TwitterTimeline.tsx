import { useEffect, useRef } from "react";

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

function loadWidgetsScript(): Promise<void> {
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

interface Props {
  handle: string;
  tweetLimit?: number;
}

export default function TwitterTimeline({ handle, tweetLimit = 3 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    loadWidgetsScript().then(() => {
      if (!cancelled && containerRef.current) {
        window.twttr?.widgets.load(containerRef.current);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [handle]);

  return (
    <div className="twitter-embed" ref={containerRef}>
      <a
        className="twitter-timeline"
        data-theme="dark"
        data-tweet-limit={tweetLimit}
        data-chrome="noheader nofooter noborders transparent"
        href={`https://twitter.com/${handle}`}
      >
        Tweets by @{handle}
      </a>
    </div>
  );
}
