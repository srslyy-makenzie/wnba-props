import { useEffect, useMemo, useState } from "react";
import type { PredictionsPayload } from "./types";
import MarketTabs from "./components/MarketTabs";
import GameCard from "./components/GameCard";
import OverviewPage from "./components/OverviewPage";

const TOP_PICK_LABELS: Record<string, string> = {
  first_basket: "FIRST BASKET",
  player_points: "TOP SCORER",
  player_rebounds: "TOP REBOUNDER",
  player_assists: "TOP PLAYMAKER",
  first_team_basket: "FIRST BASKET",
};

type Page = "overview" | "board";

export default function App() {
  const [payload, setPayload] = useState<PredictionsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeMarketId, setActiveMarketId] = useState<string | null>(null);
  const [page, setPage] = useState<Page>("overview");

  useEffect(() => {
    fetch("/data/predictions.json", { cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((data: PredictionsPayload) => {
        setPayload(data);
        const firstActive = data.markets.find((m) => m.status === "active");
        setActiveMarketId((firstActive ?? data.markets[0])?.id ?? null);
      })
      .catch((err) => setError(String(err)));
  }, []);

  const activeMarket = useMemo(
    () => payload?.markets.find((m) => m.id === activeMarketId) ?? null,
    [payload, activeMarketId],
  );

  return (
    <div className="page">
      <header className="page-head">
        <div className="title">WNBA Props — Tonight's Board</div>
        <div className="subtitle">
          {payload ? `generated ${payload.generated_at}` : error ? "load failed" : "loading…"}
        </div>
      </header>

      <nav className="page-nav" aria-label="Sections">
        <button
          className={"page-nav-tab" + (page === "overview" ? " page-nav-tab-active" : "")}
          onClick={() => setPage("overview")}
        >
          Overview
        </button>
        <button
          className={"page-nav-tab" + (page === "board" ? " page-nav-tab-active" : "")}
          onClick={() => setPage("board")}
        >
          Prop Board
        </button>
      </nav>

      {error && (
        <p className="empty-state">
          Couldn't load predictions ({error}). Run <code>python scripts/predict_today.py</code> to
          generate <code>web/public/data/predictions.json</code>.
        </p>
      )}

      {payload && page === "overview" && <OverviewPage schedule={payload.schedule} />}

      {payload && page === "board" && (
        <>
          <MarketTabs
            markets={payload.markets}
            activeId={activeMarketId ?? payload.markets[0]?.id}
            onSelect={setActiveMarketId}
          />

          {activeMarket && activeMarket.status === "coming_soon" && (
            <p className="empty-state">
              {activeMarket.label} is on the roadmap but not live yet — see docs/PRD.md.
            </p>
          )}

          {activeMarket && activeMarket.status === "active" && activeMarket.games.length === 0 && (
            <p className="empty-state">No games found for today.</p>
          )}

          {activeMarket && activeMarket.status === "active" && activeMarket.games.length > 0 && (
            <div className="board">
              {activeMarket.games.map((game) => (
                <GameCard
                  key={game.event_id}
                  game={game}
                  topPickLabel={TOP_PICK_LABELS[activeMarket.id] ?? activeMarket.label.toUpperCase()}
                />
              ))}
            </div>
          )}
        </>
      )}

      <footer>
        baseline heuristic model &middot; historical rate over a rolling lookback window &middot; not
        betting advice
      </footer>
    </div>
  );
}
