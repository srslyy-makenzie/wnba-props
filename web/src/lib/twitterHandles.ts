// Official X/Twitter handles, keyed by ESPN team abbreviation.
// Best-effort as of this writing — verify before relying on these; a
// wrong/renamed handle just means that team's embed shows nothing
// (X's widget fails silently), not a crash.
export const TEAM_TWITTER_HANDLES: Record<string, string> = {
  ATL: "AtlantaDream",
  CHI: "chicagosky",
  CONN: "connecticutsun",
  DAL: "DallasWings",
  GS: "valkyries",
  IND: "IndianaFever",
  LV: "LVAces",
  LA: "LASparks",
  MIN: "minnesotalynx",
  NY: "nyliberty",
  PHX: "PhoenixMercury",
  SEA: "seattlestorm",
  WSH: "WashMystics",
  TOR: "torontotempo",
};

// Always-shown accounts, independent of which teams are playing today.
export const FIXED_TWITTER_HANDLES = ["wnba", "ShamsCharania"];
