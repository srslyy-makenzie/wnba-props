import { useEffect, useRef } from "react";
import { loadTwitterWidgetsScript } from "../lib/twitterWidgets";

interface Props {
  url: string;
}

// Single-tweet embeds (oEmbed via widgets.js) — the same mechanism as a
// full profile timeline, but noticeably more reliable in practice. X has
// let the timeline widget degrade over the past couple years; individual
// tweet embeds still generally work. Same caveat applies either way: an
// ad/tracker blocker (uBlock, Brave Shields, Safari ITP) can still block
// platform.twitter.com and leave this as a plain link — that's the
// widget's own fallback, not a crash.
export default function TweetEmbed({ url }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    loadTwitterWidgetsScript().then(() => {
      if (!cancelled && containerRef.current) {
        window.twttr?.widgets.load(containerRef.current);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [url]);

  return (
    <div className="tweet-embed" ref={containerRef}>
      <blockquote className="twitter-tweet" data-theme="dark">
        <a href={url}>{url}</a>
      </blockquote>
    </div>
  );
}
