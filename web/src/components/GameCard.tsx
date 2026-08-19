import type { GamePrediction } from "../types";
import { badgeColor } from "../lib/badgeColor";

interface Props {
  game: GamePrediction;
  topPickLabel: string;
}

function probBarWidth(prob: number, maxProb: number): number {
  return maxProb <= 0 ? 0 : Math.round((prob / maxProb) * 100);
}

export default function GameCard({ game, topPickLabel }: Props) {
  const players = game.players;
  const top = players[0];
  const maxProb = top ? top.model_prob : 0;
  const teamIds = Object.keys(game.teams).length
    ? Object.keys(game.teams)
    : Array.from(new Set(players.map((p) => p.team_id)));

  const matchup =
    teamIds.map((id) => game.teams[id]?.display_name ?? `Team ${id}`).join(" @ ") || "Matchup TBD";

  const rosterNote = game.is_confirmed_starters
    ? "confirmed starters"
    : "full roster — starters not yet confirmed";

  return (
    <section className="game-card">
      <div className="game-card-header">
        <div className="badges">
          {teamIds.map((id) => (
            <span key={id} className="badge" style={{ background: badgeColor(id) }}>
              {game.teams[id]?.abbreviation ?? "?"}
            </span>
          ))}
        </div>
        <div className="matchup">{matchup}</div>
        <div className="roster-note">{rosterNote}</div>
      </div>

      <div className="top-pick">
        <div className="top-pick-label">{topPickLabel}</div>
        <div className="top-pick-name">{top ? top.player_name : "—"}</div>
        <div className="top-pick-prob">{top ? `${(top.model_prob * 100).toFixed(1)}%` : "—"}</div>
      </div>

      <table className="player-table">
        <thead>
          <tr>
            <th></th>
            <th>Player</th>
            <th>Hist. Rate</th>
            <th></th>
            <th>Prob.</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr key={`${p.team_id}-${p.player_name}`}>
              <td className="col-badge">
                <span className="mini-badge" style={{ background: badgeColor(p.team_id) }} />
              </td>
              <td className="col-name">{p.player_name || "Unknown"}</td>
              <td className="col-rate">{p.historical_first_basket_rate.toFixed(3)}</td>
              <td className="col-bar">
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${probBarWidth(p.model_prob, maxProb)}%` }}
                  />
                </div>
              </td>
              <td className="col-prob">{(p.model_prob * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
