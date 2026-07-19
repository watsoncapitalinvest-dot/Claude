import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { avatarUrl, playerName, type Roster } from '../../src/api/sleeper';
import { Avatar, Card, EmptyState, Loading, PositionBadge } from '../../src/components/ui';
import { managerName, useLeague } from '../../src/hooks/useLeague';
import { useValues } from '../../src/hooks/useValues';
import { useApp } from '../../src/store/AppContext';
import { colors, font, radius, spacing } from '../../src/theme';

export default function Trade() {
  const { data, loading, error } = useLeague();
  const { season } = useApp();
  const { value, loading: valLoading, projectionBased } = useValues(
    season,
    data?.league.scoring_settings,
    data?.players,
  );

  const [partnerId, setPartnerId] = useState<number | null>(null);
  const [give, setGive] = useState<Set<string>>(new Set());
  const [get, setGet] = useState<Set<string>>(new Set());

  const partners = useMemo(
    () => (data ? data.rosters.filter((r) => r.roster_id !== data.myRoster?.roster_id) : []),
    [data],
  );

  const partner: Roster | null = useMemo(
    () => partners.find((r) => r.roster_id === partnerId) ?? null,
    [partners, partnerId],
  );

  if (loading && !data) return <Loading label="Loading rosters…" />;
  if (error) return <EmptyState title="Couldn't load league" subtitle={error} />;
  if (!data?.myRoster) return <EmptyState title="No roster found" />;

  const toggle = (set: Set<string>, setter: (s: Set<string>) => void, id: string) => {
    const next = new Set(set);
    next.has(id) ? next.delete(id) : next.add(id);
    setter(next);
  };

  const giveVal = sum([...give].map(value));
  const getVal = sum([...get].map(value));
  const net = round1(getVal - giveVal);
  const verdict = judge(net, giveVal);

  const sortByValue = (ids: string[] | null) =>
    [...(ids || [])].sort((a, b) => value(b) - value(a));

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.bg }}
      contentContainerStyle={styles.content}
    >
      {valLoading ? <Text style={styles.loadingNote}>Loading player values…</Text> : null}
      {!projectionBased && !valLoading ? (
        <Text style={styles.loadingNote}>
          Season projections unavailable — values below are an ADP-based estimate.
        </Text>
      ) : null}

      {/* Verdict header */}
      <Card style={[styles.verdict, { borderColor: verdict.color }]}>
        <Text style={[styles.verdictTitle, { color: verdict.color }]}>{verdict.label}</Text>
        <Text style={styles.verdictSub}>{verdict.detail}</Text>
        <View style={styles.tallyRow}>
          <Tally label="You give" value={round1(giveVal)} />
          <Text style={styles.arrow}>⇄</Text>
          <Tally label="You get" value={round1(getVal)} tint={colors.accent} />
        </View>
        <View style={styles.netBar}>
          <View
            style={{
              flex: Math.max(giveVal, 0.01),
              backgroundColor: colors.red,
              borderTopLeftRadius: 4,
              borderBottomLeftRadius: 4,
            }}
          />
          <View
            style={{
              flex: Math.max(getVal, 0.01),
              backgroundColor: colors.accent,
              borderTopRightRadius: 4,
              borderBottomRightRadius: 4,
            }}
          />
        </View>
        <Text style={styles.netText}>
          Net for you: {net > 0 ? '+' : ''}
          {net} value pts
        </Text>
      </Card>

      {/* Partner picker */}
      <Text style={styles.sectionLabel}>Trade with</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.partnerRow}>
        {partners.map((r) => {
          const active = r.roster_id === partnerId;
          return (
            <Pressable
              key={r.roster_id}
              onPress={() => {
                setPartnerId(r.roster_id);
                setGet(new Set());
              }}
              style={[styles.partnerChip, active && styles.partnerChipActive]}
            >
              <Avatar
                uri={avatarUrl(data.usersById[r.owner_id || '']?.avatar)}
                size={30}
                fallback={managerName(r.owner_id, data.usersById)}
              />
              <Text style={[styles.partnerName, active && { color: colors.text }]} numberOfLines={1}>
                {managerName(r.owner_id, data.usersById)}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      {/* You give */}
      <Text style={styles.sectionLabel}>You give — tap to offer</Text>
      <Card style={{ paddingVertical: spacing.xs }}>
        {sortByValue(data.myRoster.players).map((id) => (
          <SelectableRow
            key={id}
            id={id}
            player={data.players[id]}
            value={value(id)}
            selected={give.has(id)}
            tint={colors.red}
            onPress={() => toggle(give, setGive, id)}
          />
        ))}
      </Card>

      {/* You get */}
      {partner ? (
        <>
          <Text style={styles.sectionLabel}>
            {managerName(partner.owner_id, data.usersById)} gives — tap to request
          </Text>
          <Card style={{ paddingVertical: spacing.xs }}>
            {sortByValue(partner.players).map((id) => (
              <SelectableRow
                key={id}
                id={id}
                player={data.players[id]}
                value={value(id)}
                selected={get.has(id)}
                tint={colors.accent}
                onPress={() => toggle(get, setGet, id)}
              />
            ))}
          </Card>
        </>
      ) : (
        <EmptyState title="Pick a trade partner above" subtitle="Then tap players from each side to build the deal." />
      )}

      <Text style={styles.footnote}>
        Values are full-season projected fantasy points under your league's scoring. A guide, not gospel —
        needs, byes, and upside are yours to weigh.
      </Text>
    </ScrollView>
  );
}

function SelectableRow({
  id,
  player,
  value,
  selected,
  tint,
  onPress,
}: {
  id: string;
  player: any;
  value: number;
  selected: boolean;
  tint: string;
  onPress: () => void;
}) {
  const pos = player?.position || player?.fantasy_positions?.[0] || null;
  return (
    <Pressable
      onPress={onPress}
      style={[styles.selRow, selected && { backgroundColor: colors.cardAlt, borderRadius: 10 }]}
    >
      <View style={[styles.check, selected && { backgroundColor: tint, borderColor: tint }]}>
        {selected ? <Text style={styles.checkMark}>✓</Text> : null}
      </View>
      <PositionBadge pos={pos} />
      <View style={{ flex: 1 }}>
        <Text style={styles.selName} numberOfLines={1}>
          {playerName(player, id)}
        </Text>
        <Text style={styles.selTeam}>{player?.team || 'FA'}</Text>
      </View>
      <Text style={styles.selValue}>{Math.round(value)}</Text>
    </Pressable>
  );
}

function Tally({ label, value, tint }: { label: string; value: number; tint?: string }) {
  return (
    <View style={{ alignItems: 'center', flex: 1 }}>
      <Text style={[styles.tallyValue, tint ? { color: tint } : null]}>{value}</Text>
      <Text style={styles.tallyLabel}>{label}</Text>
    </View>
  );
}

const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
const round1 = (x: number) => Math.round(x * 10) / 10;

function judge(net: number, giveVal: number): { label: string; detail: string; color: string } {
  const base = Math.max(giveVal, 20);
  const pct = net / base;
  if (giveVal === 0) return { label: 'Build your offer', detail: 'Tap players on each side to see the verdict.', color: colors.textFaint };
  if (pct > 0.15) return { label: 'You win this trade', detail: "You're getting meaningfully more value than you send.", color: colors.accent };
  if (pct < -0.15) return { label: "You're overpaying", detail: 'You send more value than you get back — target a sweetener.', color: colors.red };
  return { label: 'Fair deal', detail: 'Value is close to even. It comes down to fit and need.', color: colors.blue };
}

const styles = StyleSheet.create({
  content: { padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxl },
  loadingNote: { color: colors.textFaint, fontSize: font.tiny, textAlign: 'center' },
  verdict: { gap: spacing.sm, alignItems: 'center' },
  verdictTitle: { fontSize: font.h2, fontWeight: '900' },
  verdictSub: { color: colors.textDim, fontSize: font.small, textAlign: 'center' },
  tallyRow: { flexDirection: 'row', alignItems: 'center', alignSelf: 'stretch', marginTop: spacing.sm },
  arrow: { color: colors.textFaint, fontSize: 22, paddingHorizontal: spacing.sm },
  tallyValue: { color: colors.text, fontSize: font.h1, fontWeight: '900' },
  tallyLabel: { color: colors.textFaint, fontSize: font.tiny, textTransform: 'uppercase' },
  netBar: { flexDirection: 'row', height: 8, alignSelf: 'stretch', borderRadius: 4, overflow: 'hidden', marginTop: spacing.xs },
  netText: { color: colors.textDim, fontSize: font.small, fontWeight: '700' },
  sectionLabel: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: spacing.sm,
    marginLeft: spacing.xs,
  },
  partnerRow: { gap: spacing.sm, paddingVertical: spacing.xs },
  partnerChip: {
    alignItems: 'center',
    gap: 4,
    padding: spacing.sm,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    width: 84,
  },
  partnerChipActive: { borderColor: colors.accent, backgroundColor: colors.cardAlt },
  partnerName: { color: colors.textDim, fontSize: font.tiny, fontWeight: '600', textAlign: 'center' },
  selRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm, paddingHorizontal: spacing.xs },
  check: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkMark: { color: '#04210d', fontSize: 14, fontWeight: '900' },
  selName: { color: colors.text, fontSize: font.body, fontWeight: '600' },
  selTeam: { color: colors.textFaint, fontSize: font.tiny },
  selValue: { color: colors.text, fontSize: font.h3, fontWeight: '800', width: 44, textAlign: 'right', fontVariant: ['tabular-nums'] },
  footnote: { color: colors.textFaint, fontSize: font.tiny, textAlign: 'center', lineHeight: 16, marginTop: spacing.sm },
});
