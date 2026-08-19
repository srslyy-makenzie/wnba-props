// Deterministic per-team accent color, derived from team_id so the same
// team always gets the same badge color across renders without needing a
// real team-color lookup table.
const BADGE_PALETTE = [
  "#E8590C", // burnt orange
  "#2B8A9E", // teal
  "#C2255C", // magenta
  "#5C7CFA", // periwinkle
  "#37B24D", // green
  "#F08C00", // amber
  "#845EF7", // violet
  "#1098AD", // cyan
];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function badgeColor(teamId: string): string {
  return BADGE_PALETTE[hashString(teamId) % BADGE_PALETTE.length];
}
