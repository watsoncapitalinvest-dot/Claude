import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  getDraftPicks,
  getLeagueDrafts,
  playerName,
  type Draft,
  type DraftPick,
} from '../../src/api/sleeper';
import { Card, EmptyState, Loading, Pill, PositionBadge } from '../../src/components/ui';
import { useLeague } from '../../src/hooks/useLeague';
import { startingNeeds, useValues } from '../../src/hooks/useValues';
import { useApp } from '../../src/store/AppContext';
import { colors, font, radius, spacing } from '../../src/theme';

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF'];

export default function DraftBoard() {
  const { data, loading, error } = useLeague();
  const { season, user } = useApp();
  const { value, ranked, loading: valLoading, projectionBased } = useValues(
    season,
    data?.league.scoring_settings,
    data?.players,
  );

  const [draft, setDraft] = useState<Draft | null>(null);
  const [picks, setPicks] = useState<DraftPick[]>([]);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [posFilter, setPosFilter] = useState('ALL');

  const leagueId = data?.league.league_id;

  useEffect(() => {
    if (!leagueId) return;
    let cancelled = false;
    (async () => {
      try {
        const drafts = await getLeagueDrafts(leagueId);
        const latest = pickLatestDraft(drafts);
        if (cancelled) return;
        setDraft(latest);
        if (latest) {
          const p = await getDraftPicks(latest.draft_id);
          if (!cancelled) setPicks(p);
        }
      } catch {
        // no draft available — board still works as a cheat sheet
      } finally {
        if (!cancelled) setDraftLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [leagueId]);

  const draftedIds = useMemo(() => new Set(picks.map((p) => p.player_id)), [picks]);

  const myPicks = useMemo(
    () => (user ? picks.filter((p) => p.picked_by === user.user_id) : []),
    [picks, user],
  );

  // Best available, filtered, capped, with tier breaks.
  const board = useMemo(() => {
    if (!data) return [];
    const available = ranked.filter((id) => {
      if (draftedIds.has(id)) return false;
      if (posFilter === 'ALL') return true;
      const p = data.players[id];
      const pos = p?.position || p?.fantasy_positions?.[0];
      return pos === posFilter;
    });
    const top = available.slice(0, 60);
    const topValue = top.length ? value(top[0]) : 0;
    const gap = Math.max(6, topValue * 0.045);
    let tier = 1;
    return top.map((id, i) => {
      if (i > 0 && value(top[i - 1]) - value(id) > gap) tier += 1;
      return { id, tier };
    });
  }, [data, ranked, draftedIds, posFilter, value]);

  // My roster needs (draft context).
  const needs = useMemo(() => {
    if (!data) return [];
    const req = startingNeeds(data.league.roster_positions);
    const have: Record<string, number> = {};
    for (const p of myPicks) {
      const pos = data.players[p.player_id]?.position;
      if (pos) have[pos] = (have[pos] || 0) + 1;
    }
    const out: { pos: string; deficit: number }[] = [];
    for (const pos of ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']) {
      const need = req[pos] || 0;
      const flexNeed = pos === 'RB' || pos === 'WR' || pos === 'TE' ? req.FLEX || 0 : 0;
      const target = need + (flexNeed ? 1 : 0);
      const deficit = target - (have[pos] || 0);
      if (deficit > 0) out.push({ pos, deficit });
    }
    return out.sort((a, b) => b.deficit - a.deficit);
  }, [data, myPicks]);

  if (loading && !data) return <Loading label="Loading league…" />;
  if (error) return <EmptyState title="Couldn't load league" subtitle={error} />;
  if (!data) return <EmptyState title="No league data" />;
  if (!draftLoaded || valLoading) return <Loading label="Building the draft board…" />;

  const status = draft?.status;
  const statusInfo =
    status === 'drafting'
      ? { label: 'DRAFT LIVE', color: colors.accent }
      : status === 'complete'
        ? { label: 'DRAFT COMPLETE', color: colors.textFaint }
        : { label: status === 'pre_draft' ? 'PRE-DRAFT' : 'CHEAT SHEET', color: colors.blue };

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.bg }}
      contentContainerStyle={styles.content}
      stickyHeaderIndices={[2]}
    >
      {/* Status + needs */}
      <Card style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm }}>
          <Pill label={statusInfo.label} color={statusInfo.color} />
          <Text style={styles.statusText}>
            {picks.length > 0 ? `${picks.length} picks made` : 'No picks yet'}
            {draft ? ` · ${draft.type} draft` : ''}
          </Text>
        </View>
        <Text style={styles.needsLabel}>Your roster needs</Text>
        {needs.length > 0 ? (
          <View style={styles.needsRow}>
            {needs.map((n) => (
              <View key={n.pos} style={styles.needChip}>
                <PositionBadge pos={n.pos} />
                <Text style={styles.needCount}>×{n.deficit}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.needsMet}>Starting slots filled — draft best available or for depth.</Text>
        )}
        {!projectionBased ? (
          <Text style={styles.estimateNote}>
            Season projections unavailable — ranks use an ADP-based estimate.
          </Text>
        ) : null}
      </Card>

      <Text style={styles.boardTitle}>Best Available</Text>

      {/* Sticky position filter */}
      <View style={styles.filterBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterRow}>
          {POSITIONS.map((pos) => {
            const active = pos === posFilter;
            return (
              <Pressable
                key={pos}
                onPress={() => setPosFilter(pos)}
                style={[styles.filterChip, active && styles.filterChipActive]}
              >
                <Text style={[styles.filterText, active && { color: '#04210d' }]}>{pos}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {/* Board */}
      <Card style={{ paddingVertical: spacing.xs }}>
        {board.length === 0 ? (
          <EmptyState title="No players available" subtitle="Try a different position filter." />
        ) : (
          board.map((row, i) => {
            const p = data.players[row.id];
            const pos = p?.position || p?.fantasy_positions?.[0] || null;
            const newTier = i === 0 || board[i - 1].tier !== row.tier;
            return (
              <View key={row.id}>
                {newTier ? (
                  <View style={styles.tierBreak}>
                    <Text style={styles.tierText}>TIER {row.tier}</Text>
                    <View style={styles.tierLine} />
                  </View>
                ) : null}
                <View style={styles.playerRow}>
                  <Text style={styles.overall}>{i + 1}</Text>
                  <PositionBadge pos={pos} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.playerName} numberOfLines={1}>
                      {playerName(p, row.id)}
                    </Text>
                    <Text style={styles.playerTeam}>
                      {p?.team || 'FA'}
                      {p?.years_exp === 0 ? ' · Rookie' : ''}
                    </Text>
                  </View>
                  <Text style={styles.playerValue}>{Math.round(value(row.id))}</Text>
                </View>
              </View>
            );
          })
        )}
      </Card>

      <Text style={styles.footnote}>
        Value = projected full-season fantasy points under your league's scoring. Live drafts update as picks
        come in — pull to refresh.
      </Text>
    </ScrollView>
  );
}

function pickLatestDraft(drafts: Draft[]): Draft | null {
  if (!drafts || drafts.length === 0) return null;
  // Prefer an in-progress draft, else the newest by season.
  const live = drafts.find((d) => d.status === 'drafting');
  if (live) return live;
  return [...drafts].sort((a, b) => Number(b.season) - Number(a.season))[0];
}

const styles = StyleSheet.create({
  content: { padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxl },
  statusText: { color: colors.textDim, fontSize: font.small, flex: 1 },
  needsLabel: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  needsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  needChip: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  needCount: { color: colors.text, fontSize: font.small, fontWeight: '800' },
  needsMet: { color: colors.accent, fontSize: font.small },
  estimateNote: { color: colors.textFaint, fontSize: font.tiny },
  boardTitle: { color: colors.text, fontSize: font.h2, fontWeight: '900', marginTop: spacing.sm },
  filterBar: { backgroundColor: colors.bg, paddingVertical: spacing.xs },
  filterRow: { gap: spacing.sm },
  filterChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgElevated,
  },
  filterChipActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  filterText: { color: colors.textDim, fontSize: font.small, fontWeight: '800' },
  tierBreak: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingTop: spacing.md, paddingBottom: spacing.xs, paddingHorizontal: spacing.xs },
  tierText: { color: colors.amber, fontSize: font.tiny, fontWeight: '900', letterSpacing: 1 },
  tierLine: { flex: 1, height: StyleSheet.hairlineWidth, backgroundColor: colors.border },
  playerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm, paddingHorizontal: spacing.xs },
  overall: { color: colors.textFaint, fontSize: font.small, fontWeight: '800', width: 26, textAlign: 'center' },
  playerName: { color: colors.text, fontSize: font.body, fontWeight: '600' },
  playerTeam: { color: colors.textFaint, fontSize: font.tiny },
  playerValue: { color: colors.text, fontSize: font.h3, fontWeight: '800', width: 44, textAlign: 'right', fontVariant: ['tabular-nums'] },
  footnote: { color: colors.textFaint, fontSize: font.tiny, textAlign: 'center', lineHeight: 16, marginTop: spacing.sm },
});
