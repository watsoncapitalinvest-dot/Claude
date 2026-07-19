/**
 * The News Room engine.
 *
 * Given a week's Sleeper matchups plus each player's real box-score stats, this
 * builds a full fantasy newsletter — a lead recap, a "game story" per matchup,
 * and league awards. Every sentence is grounded in actual numbers: final fantasy
 * scores, real stat lines (yards / TDs / catches), and expectation gaps (what a
 * player was projected vs. what he delivered). No facts are invented.
 *
 * Output is deterministic: template variety is seeded from stable values
 * (scores, ids) so a given week reads the same every time you open it.
 */
import type { League, LeagueUser, Player, PlayerMap, Roster, Matchup } from '../api/sleeper';
import { scoreStats } from './scoring';
import { avatarUrl } from '../api/sleeper';
import { playerName } from '../api/sleeper';
import { bustAdjective, hasProduction, performanceVerb, statLine } from './statline';

type Stats = Record<string, number>;

export interface PerfEntry {
  id: string;
  player: Player | undefined;
  pos: string;
  points: number;
  projected: number;
  stats: Stats | undefined;
  line: string;
}

export interface TeamRecap {
  rosterId: number;
  manager: string;
  avatar: string | null;
  score: number;
  starters: PerfEntry[];
  bench: PerfEntry[];
  top: PerfEntry | null;
  bust: PerfEntry | null;
  benchRegret: { bench: PerfEntry; starter: PerfEntry; diff: number } | null;
}

export interface GameStory {
  id: string;
  headline: string;
  dek: string;
  paragraphs: string[];
  winner: TeamRecap;
  loser: TeamRecap;
  tie: boolean;
  margin: number;
  combined: number;
}

export interface Award {
  emoji: string;
  title: string;
  name: string;
  detail: string;
}

export interface Newsletter {
  week: number;
  leagueName: string;
  edition: string;
  lead: { headline: string; standfirst: string; paragraphs: string[] };
  stories: GameStory[];
  awards: Award[];
  hasData: boolean;
}

function seededPick<T>(arr: T[], seed: number): T {
  return arr[Math.abs(Math.round(seed)) % arr.length];
}

const round1 = (x: number) => Math.round(x * 10) / 10;

export interface NewsletterInput {
  week: number;
  league: League;
  matchups: Matchup[];
  rosters: Roster[];
  usersById: Record<string, LeagueUser>;
  players: PlayerMap;
  weeklyStats: Record<string, Stats>;
  weeklyProjections: Record<string, Stats>;
}

export function buildNewsletter(input: NewsletterInput): Newsletter {
  const { week, league, matchups, rosters, usersById, players, weeklyStats, weeklyProjections } =
    input;
  const scoring = league.scoring_settings;
  const rosterById = new Map(rosters.map((r) => [r.roster_id, r]));

  const managerFor = (rosterId: number): { name: string; avatar: string | null } => {
    const roster = rosterById.get(rosterId);
    const u = roster?.owner_id ? usersById[roster.owner_id] : undefined;
    return {
      name: u?.metadata?.team_name || u?.display_name || `Team ${rosterId}`,
      avatar: avatarUrl(u?.avatar ?? null),
    };
  };

  const pointsFor = (entry: Matchup, id: string): number => {
    if (entry.players_points && typeof entry.players_points[id] === 'number') {
      return entry.players_points[id];
    }
    return scoreStats(weeklyStats[id], scoring);
  };

  const posOf = (id: string): string =>
    players[id]?.position || players[id]?.fantasy_positions?.[0] || '';

  const makeEntry = (entry: Matchup, id: string): PerfEntry => {
    const stats = weeklyStats[id];
    const pos = posOf(id);
    const points = round1(pointsFor(entry, id));
    const projected = round1(scoreStats(weeklyProjections[id], scoring));
    return { id, player: players[id], pos, points, projected, stats, line: statLine(pos, stats) };
  };

  const buildTeam = (entry: Matchup): TeamRecap => {
    const starterIds = (entry.starters || []).filter(Boolean);
    const allIds = entry.players || [];
    const benchIds = allIds.filter((id) => id && !starterIds.includes(id));

    const starters = starterIds.map((id) => makeEntry(entry, id));
    const bench = benchIds.map((id) => makeEntry(entry, id));
    const score = round1(
      entry.points && entry.points > 0
        ? entry.points
        : starters.reduce((s, e) => s + e.points, 0),
    );
    const { name, avatar } = managerFor(entry.roster_id);

    const scorers = [...starters].sort((a, b) => b.points - a.points);
    const top = scorers[0] ?? null;

    // Bust: the skill starter who most badly missed his projection (projected a
    // real total, delivered far less). Kickers/defenses are exempt.
    const bustPool = starters.filter(
      (e) => ['QB', 'RB', 'WR', 'TE'].includes(e.pos) && e.projected >= 8,
    );
    bustPool.sort((a, b) => a.points - a.projected - (b.points - b.projected));
    const bust = bustPool.length && bustPool[0].points < bustPool[0].projected - 5 ? bustPool[0] : null;

    // Bench regret: best bench score vs the weakest starter of a matching role.
    let benchRegret: TeamRecap['benchRegret'] = null;
    const bestBench = [...bench].sort((a, b) => b.points - a.points)[0];
    if (bestBench) {
      const weakStarter = [...starters]
        .filter((s) => flexMatch(s.pos, bestBench.pos))
        .sort((a, b) => a.points - b.points)[0];
      if (weakStarter && bestBench.points - weakStarter.points >= 6) {
        benchRegret = {
          bench: bestBench,
          starter: weakStarter,
          diff: round1(bestBench.points - weakStarter.points),
        };
      }
    }

    return { rosterId: entry.roster_id, manager: name, avatar, score, starters, bench, top, bust, benchRegret };
  };

  // Group matchup entries into head-to-head pairs.
  const byMatchup = new Map<number, Matchup[]>();
  for (const m of matchups) {
    if (m.matchup_id == null) continue;
    const list = byMatchup.get(m.matchup_id) || [];
    list.push(m);
    byMatchup.set(m.matchup_id, list);
  }

  const anyPoints = matchups.some((m) => (m.points || 0) > 0);

  const stories: GameStory[] = [];
  for (const [mid, pair] of byMatchup) {
    if (pair.length < 2) continue;
    const a = buildTeam(pair[0]);
    const b = buildTeam(pair[1]);
    const [winner, loser] = a.score >= b.score ? [a, b] : [b, a];
    const tie = a.score === b.score;
    const margin = round1(Math.abs(a.score - b.score));
    const combined = round1(a.score + b.score);
    stories.push(writeGameStory({ mid, winner, loser, tie, margin, combined, week }));
  }

  // Order stories: closest / highest-drama first.
  stories.sort((a, b) => dramaScore(b) - dramaScore(a));

  const lead = writeLead(stories, week, league.name);
  const awards = writeAwards(stories);

  return {
    week,
    leagueName: league.name,
    edition: `Week ${week} Edition`,
    lead,
    stories,
    awards,
    hasData: anyPoints && stories.length > 0,
  };
}

function flexMatch(a: string, b: string): boolean {
  if (a === b) return true;
  const flex = new Set(['RB', 'WR', 'TE']);
  return flex.has(a) && flex.has(b);
}

function dramaScore(s: GameStory): number {
  // Reward high combined scoring and punish blowouts a little.
  return s.combined - s.margin * 0.5;
}

function writeGameStory(ctx: {
  mid: number;
  winner: TeamRecap;
  loser: TeamRecap;
  tie: boolean;
  margin: number;
  combined: number;
  week: number;
}): GameStory {
  const { winner, loser, tie, margin, combined } = ctx;
  const seed = Math.round(winner.score * 10 + loser.score + winner.rosterId);
  const paragraphs: string[] = [];

  const blowout = margin >= 35;
  const nailBiter = margin > 0 && margin <= 6;

  // Headline
  let headline: string;
  if (tie) {
    headline = `${winner.manager} and ${loser.manager} play to a stalemate`;
  } else if (blowout) {
    headline = seededPick(
      [
        `${winner.manager} runs riot over ${loser.manager}`,
        `${winner.manager} leaves no doubt against ${loser.manager}`,
        `${loser.manager} steamrolled by ${winner.manager}`,
      ],
      seed,
    );
  } else if (nailBiter) {
    headline = seededPick(
      [
        `${winner.manager} survives ${loser.manager} by ${margin}`,
        `${winner.manager} edges ${loser.manager} in a photo finish`,
        `${loser.manager} falls ${margin} short against ${winner.manager}`,
      ],
      seed,
    );
  } else {
    headline = seededPick(
      [
        `${winner.manager} handles ${loser.manager}`,
        `${winner.manager} takes care of business vs. ${loser.manager}`,
        `${winner.manager} pulls away from ${loser.manager}`,
      ],
      seed,
    );
  }

  // Dek
  const star = winner.top;
  const dek = star
    ? `${playerName(star.player, star.id)} leads the way with ${star.points}.`
    : `Final: ${winner.score}–${loser.score}.`;

  // Paragraph 1 — the result + winner's star, with a real stat line.
  const scoreline = tie
    ? `deadlocked at ${winner.score} apiece`
    : `${winner.score}–${loser.score}`;
  let p1 = tie
    ? `${winner.manager} and ${loser.manager} couldn't be separated, ${scoreline}. `
    : `${winner.manager} ${blowout ? 'dismantled' : nailBiter ? 'outlasted' : 'beat'} ${loser.manager} ${scoreline}${
        nailBiter ? `, a ${margin}-point thriller` : ''
      }. `;
  if (star && star.points > 0) {
    const verb = performanceVerb(star.points);
    p1 += `${playerName(star.player, star.id)} ${verb} ${star.points}`;
    if (star.line && hasProduction(star.stats)) p1 += ` on ${star.line}`;
    p1 += star.pos === 'DEF' ? ', anchoring the win.' : ', pacing the roster.';
  }
  paragraphs.push(p1.trim());

  // Paragraph 2 — the losing side: their bright spot and their letdown.
  const loserStar = loser.top;
  let p2 = '';
  if (loserStar && loserStar.points > 0) {
    p2 += tie
      ? `${playerName(loserStar.player, loserStar.id)} kept ${loser.manager} level with ${loserStar.points}`
      : `${loserStar.player ? playerName(loserStar.player, loserStar.id) : 'The top scorer'} did what he could for ${loser.manager}, posting ${loserStar.points}`;
    if (loserStar.line && hasProduction(loserStar.stats)) p2 += ` (${loserStar.line})`;
    p2 += tie ? '. ' : `, but it wasn't enough. `;
  }
  if (loser.bust) {
    const b = loser.bust;
    p2 += `The dagger was ${playerName(b.player, b.id)}, ${bustAdjective(b.points)} — projected ${b.projected}, delivered just ${b.points}. `;
  }
  if (p2.trim()) paragraphs.push(p2.trim());

  // Paragraph 3 — bench regret or a closing beat.
  let p3 = '';
  if (loser.benchRegret) {
    const r = loser.benchRegret;
    p3 = `${loser.manager} will replay this one all week: ${playerName(r.bench.player, r.bench.id)} dropped ${r.bench.points} from the bench while ${playerName(r.starter.player, r.starter.id)} managed ${r.starter.points} in the lineup — a ${r.diff}-point what-if in a ${margin}-point loss.`;
  } else if (winner.benchRegret) {
    const r = winner.benchRegret;
    p3 = `Even in victory, ${winner.manager} left points on the table — ${playerName(r.bench.player, r.bench.id)}'s ${r.bench.points} watched from the bench.`;
  } else if (blowout && winner.top) {
    p3 = `For ${loser.manager}, it's back to the drawing board. For ${winner.manager}, everything clicked.`;
  }
  if (p3.trim()) paragraphs.push(p3.trim());

  return {
    id: `game-${ctx.mid}`,
    headline,
    dek,
    paragraphs,
    winner,
    loser,
    tie,
    margin,
    combined,
  };
}

function writeLead(
  stories: GameStory[],
  week: number,
  leagueName: string,
): Newsletter['lead'] {
  if (stories.length === 0) {
    return {
      headline: `Week ${week} around ${leagueName}`,
      standfirst: 'The scores are still coming in.',
      paragraphs: [],
    };
  }

  // Superlatives across the week.
  const allTeams = stories.flatMap((s) => [s.winner, s.loser]);
  const highTeam = [...allTeams].sort((a, b) => b.score - a.score)[0];
  const lowTeam = [...allTeams].sort((a, b) => a.score - b.score)[0];
  const closest = [...stories].sort((a, b) => a.margin - b.margin)[0];
  const biggest = [...stories].sort((a, b) => b.margin - a.margin)[0];

  const allStarters = allTeams.flatMap((t) => t.starters);
  const topPlayer = [...allStarters].sort((a, b) => b.points - a.points)[0];

  const headline = seededPick(
    [
      `Week ${week}: ${highTeam.manager} sets the pace`,
      `Week ${week} around the league: chalk, chaos, and a ${closest.margin}-point thriller`,
      `The Week ${week} wrap: ${topPlayer ? playerName(topPlayer.player, topPlayer.id) : 'the studs'} steal the show`,
    ],
    Math.round(highTeam.score + week),
  );

  const standfirst = `${leagueName} · Week ${week} · your automated front-office briefing`;

  const paragraphs: string[] = [];
  let p1 = `${highTeam.manager} posted the week's top score at ${highTeam.score}`;
  if (topPlayer && topPlayer.points > 0) {
    p1 += `, powered by ${playerName(topPlayer.player, topPlayer.id)}'s ${topPlayer.points}`;
    if (topPlayer.line && hasProduction(topPlayer.stats)) p1 += ` (${topPlayer.line})`;
  }
  p1 += `. At the other end, ${lowTeam.manager} managed only ${lowTeam.score}.`;
  paragraphs.push(p1);

  if (closest && closest !== biggest) {
    paragraphs.push(
      `The nerviest finish belonged to ${closest.winner.manager}, who slipped past ${closest.loser.manager} by ${closest.margin}. The week's most lopsided result: ${biggest.winner.manager} over ${biggest.loser.manager} by ${biggest.margin}.`,
    );
  }

  return { headline, standfirst, paragraphs };
}

function writeAwards(stories: GameStory[]): Award[] {
  if (stories.length === 0) return [];
  const teams = stories.flatMap((s) => [s.winner, s.loser]);
  const starters = teams.flatMap((t) => t.starters);
  const awards: Award[] = [];

  const topTeam = [...teams].sort((a, b) => b.score - a.score)[0];
  if (topTeam) {
    awards.push({
      emoji: '👑',
      title: 'Team of the Week',
      name: topTeam.manager,
      detail: `${topTeam.score} points${topTeam.top ? ` · led by ${playerName(topTeam.top.player, topTeam.top.id)} (${topTeam.top.points})` : ''}`,
    });
  }

  const topPlayer = [...starters].sort((a, b) => b.points - a.points)[0];
  if (topPlayer && topPlayer.points > 0) {
    awards.push({
      emoji: '🔥',
      title: 'Performance of the Week',
      name: playerName(topPlayer.player, topPlayer.id),
      detail: `${topPlayer.points} pts${topPlayer.line ? ` · ${topPlayer.line}` : ''}`,
    });
  }

  // Biggest bust across the league (worst miss vs projection among started skill players).
  const busts = teams.map((t) => t.bust).filter(Boolean) as PerfEntry[];
  const worstBust = [...busts].sort((a, b) => a.points - a.projected - (b.points - b.projected))[0];
  if (worstBust) {
    awards.push({
      emoji: '🧊',
      title: 'Faceplant of the Week',
      name: playerName(worstBust.player, worstBust.id),
      detail: `Projected ${worstBust.projected}, scored ${worstBust.points}`,
    });
  }

  const closest = [...stories].sort((a, b) => a.margin - b.margin)[0];
  if (closest && !closest.tie) {
    awards.push({
      emoji: '😰',
      title: 'Nail-Biter',
      name: `${closest.winner.manager} def. ${closest.loser.manager}`,
      detail: `Margin of ${closest.margin}`,
    });
  }

  const regrets = teams
    .map((t) => t.benchRegret)
    .filter(Boolean) as NonNullable<TeamRecap['benchRegret']>[];
  const worstRegret = [...regrets].sort((a, b) => b.diff - a.diff)[0];
  if (worstRegret) {
    awards.push({
      emoji: '🪑',
      title: 'Bench Blunder',
      name: playerName(worstRegret.bench.player, worstRegret.bench.id),
      detail: `${worstRegret.bench.points} pts stranded on the bench`,
    });
  }

  return awards;
}
