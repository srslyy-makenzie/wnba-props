import { useMemo } from "react";
import type { ScheduleGame } from "../types";
import { badgeColor } from "../lib/badgeColor";
import { TEAM_TWITTER_HANDLES, FIXED_TWITTER_HANDLES } from "../lib/twitterHandles";
import TwitterTimeline from "./TwitterTimeline";

interface Props {
  schedule: ScheduleGame[];
}

function ScheduleCard({ game }: { game: ScheduleGame }) {
  const teamIds = Object.keys(game.teams);
  const away = teamIds.map((id) => game.teams[id]).find((t) => t.home_away === "away");
  const home = teamIds.map((id) => game.teams[id]).find((t) => t.home_away === "home");
  const ordered = [away, home].filter((t): t is NonNullable<typeof away> => Boolean(t));

  return (
    <section className="schedule-card">
      <div className="schedule-card-time">{game.start_time_display || game.status}</div>
      <div className="schedule-card-matchup">
        {ordered.map((team, i) => (
          <span key={team.abbreviation} className="schedule-team">
            <span className="mini-badge" style={{ background: badgeColor(team.abbreviation) }} />
            {team.display_name}
            {team.record && <span className="schedule-record">({team.record})</span>}
            {i === 0 && <span className="schedule-at">@</span>}
          </span>
        ))}
      </div>
      {game.venue?.name && (
        <div className="schedule-venue">
          {game.venue.name}
          {game.venue.city ? ` — ${game.venue.city}${game.venue.state ? `, ${game.venue.state}` : ""}` : ""}
        </div>
      )}
      {game.broadcasts.length > 0 && (
        <div className="schedule-broadcast">{game.broadcasts.join(" · ")}</div>
      )}
    </section>
  );
}

export default function OverviewPage({ schedule = [] }: Props) {
  const twitterHandles = useMemo(() => {
    const todaysTeamAbbrs = new Set(
      schedule.flatMap((g) => Object.values(g.teams).map((t) => t.abbreviation)),
    );
    const teamHandles = [...todaysTeamAbbrs]
      .map((abbr) => TEAM_TWITTER_HANDLES[abbr])
      .filter((h): h is string => Boolean(h));
    return [...FIXED_TWITTER_HANDLES, ...teamHandles];
  }, [schedule]);

  return (
    <div className="overview">
      <section className="overview-section">
        <h2 className="overview-heading">Today's Games</h2>
        {schedule.length === 0 ? (
          <p className="empty-state">No WNBA games scheduled today.</p>
        ) : (
          <div className="schedule-board">
            {schedule.map((game) => (
              <ScheduleCard key={game.event_id} game={game} />
            ))}
          </div>
        )}
      </section>

      <section className="overview-section">
        <h2 className="overview-heading">Latest from X</h2>
        <div className="twitter-board">
          {twitterHandles.map((handle) => (
            <TwitterTimeline key={handle} handle={handle} />
          ))}
        </div>
      </section>
    </div>
  );
}
