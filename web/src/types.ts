export interface TeamInfo {
  display_name: string;
  abbreviation: string;
}

export interface PlayerPrediction {
  player_name: string;
  team_id: string;
  historical_first_basket_rate: number;
  model_prob: number;
  odds_american: number | null;
  market_prob: number | null;
  edge: number | null;
  ev: number | null;
  is_positive_ev: boolean | null;
}

export interface GamePrediction {
  event_id: string;
  teams: Record<string, TeamInfo>;
  is_confirmed_starters: boolean;
  odds_note?: string;
  players: PlayerPrediction[];
}

export type MarketStatus = "active" | "coming_soon";

export interface Market {
  id: string;
  label: string;
  description: string;
  status: MarketStatus;
  games: GamePrediction[];
}

export interface ScheduleTeamInfo {
  display_name: string;
  abbreviation: string;
  home_away: "home" | "away" | null;
  record: string | null;
}

export interface ScheduleVenue {
  name: string | null;
  city: string | null;
  state: string | null;
}

export interface ScheduleGame {
  event_id: string;
  start_time_iso: string;
  start_time_display: string;
  status: string;
  venue: ScheduleVenue | null;
  broadcasts: string[];
  teams: Record<string, ScheduleTeamInfo>;
}

export interface PredictionsPayload {
  generated_at: string;
  schedule: ScheduleGame[];
  markets: Market[];
}
