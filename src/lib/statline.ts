/**
 * Turns a Sleeper stat bag into a human, broadcast-style stat line by position,
 * plus small helpers the narrative engine uses to describe a performance
 * ("erupted for", "quietly chipped in"). Everything here is derived from real
 * box-score numbers Sleeper reports — no invented facts.
 */

type Stats = Record<string, number>;

const n = (s: Stats, k: string): number => (typeof s[k] === 'number' ? s[k] : 0);

/** Compact box-score line, e.g. "27/38, 341 yds, 3 TD, 1 INT" for a QB. */
export function statLine(pos: string | null | undefined, s: Stats | undefined): string {
  if (!s) return '';
  const parts: string[] = [];

  if (pos === 'QB') {
    const cmp = n(s, 'pass_cmp');
    const att = n(s, 'pass_att');
    if (att) parts.push(`${cmp}/${att}`);
    if (n(s, 'pass_yd')) parts.push(`${Math.round(n(s, 'pass_yd'))} pass yds`);
    if (n(s, 'pass_td')) parts.push(`${n(s, 'pass_td')} pass TD`);
    if (n(s, 'pass_int')) parts.push(`${n(s, 'pass_int')} INT`);
    if (n(s, 'rush_yd') >= 15 || n(s, 'rush_td')) {
      parts.push(rushFragment(s));
    }
    return parts.filter(Boolean).join(', ');
  }

  if (pos === 'RB') {
    if (n(s, 'rush_att')) parts.push(rushFragment(s));
    if (n(s, 'rec')) parts.push(recFragment(s));
    return parts.filter(Boolean).join(' · ');
  }

  if (pos === 'WR' || pos === 'TE') {
    if (n(s, 'rec') || n(s, 'rec_tgt')) parts.push(recFragment(s));
    if (n(s, 'rush_yd') || n(s, 'rush_td')) parts.push(rushFragment(s));
    return parts.filter(Boolean).join(' · ');
  }

  if (pos === 'K') {
    const fgm = n(s, 'fgm');
    const fga = n(s, 'fga');
    if (fga) parts.push(`${fgm}/${fga} FG`);
    if (n(s, 'xpm')) parts.push(`${n(s, 'xpm')} XP`);
    if (n(s, 'fgm_50p')) parts.push(`${n(s, 'fgm_50p')} from 50+`);
    return parts.filter(Boolean).join(', ');
  }

  if (pos === 'DEF') {
    if (n(s, 'sack')) parts.push(`${n(s, 'sack')} sk`);
    if (n(s, 'int')) parts.push(`${n(s, 'int')} INT`);
    if (n(s, 'ff')) parts.push(`${n(s, 'ff')} FF`);
    if (n(s, 'fum_rec')) parts.push(`${n(s, 'fum_rec')} FR`);
    if (n(s, 'def_td')) parts.push(`${n(s, 'def_td')} TD`);
    if (s.pts_allow !== undefined) parts.push(`${n(s, 'pts_allow')} pts allowed`);
    return parts.filter(Boolean).join(', ');
  }

  return '';
}

function rushFragment(s: Stats): string {
  const att = n(s, 'rush_att');
  const yd = Math.round(n(s, 'rush_yd'));
  const td = n(s, 'rush_td');
  let f = att ? `${att} car, ${yd} rush yds` : `${yd} rush yds`;
  if (td) f += `, ${td} TD`;
  return f;
}

function recFragment(s: Stats): string {
  const rec = n(s, 'rec');
  const yd = Math.round(n(s, 'rec_yd'));
  const td = n(s, 'rec_td');
  const tgt = n(s, 'rec_tgt');
  let f = `${rec} rec, ${yd} yds`;
  if (td) f += `, ${td} TD`;
  if (tgt) f += ` (${tgt} tgt)`;
  return f;
}

/** True if the line has any real production worth mentioning. */
export function hasProduction(s: Stats | undefined): boolean {
  if (!s) return false;
  return (
    n(s, 'pass_yd') > 0 ||
    n(s, 'rush_yd') > 0 ||
    n(s, 'rec') > 0 ||
    n(s, 'fgm') > 0 ||
    n(s, 'sack') > 0 ||
    n(s, 'def_td') > 0
  );
}

/** A verb describing how big a fantasy day was, given points scored. */
export function performanceVerb(points: number): string {
  if (points >= 30) return 'detonated for';
  if (points >= 24) return 'erupted for';
  if (points >= 18) return 'went off for';
  if (points >= 12) return 'delivered';
  if (points >= 7) return 'chipped in';
  if (points >= 3) return 'managed just';
  return 'was held to';
}

/** A short adjective for a disappointing start given points scored. */
export function bustAdjective(points: number): string {
  if (points <= 2) return 'a total no-show';
  if (points <= 5) return 'a crushing dud';
  if (points <= 8) return 'a quiet letdown';
  return 'underwhelming';
}
