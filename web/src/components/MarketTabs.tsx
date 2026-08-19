import type { Market } from "../types";

interface Props {
  markets: Market[];
  activeId: string;
  onSelect: (id: string) => void;
}

export default function MarketTabs({ markets, activeId, onSelect }: Props) {
  return (
    <nav className="market-tabs" aria-label="Prop markets">
      {markets.map((market) => (
        <button
          key={market.id}
          className={
            "market-tab" +
            (market.id === activeId ? " market-tab-active" : "") +
            (market.status === "coming_soon" ? " market-tab-soon" : "")
          }
          onClick={() => onSelect(market.id)}
          title={market.description}
        >
          {market.label}
          {market.status === "coming_soon" && <span className="market-tab-badge">soon</span>}
        </button>
      ))}
    </nav>
  );
}
