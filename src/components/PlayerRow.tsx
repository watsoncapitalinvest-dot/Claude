import { StyleSheet, Text, View } from 'react-native';
import type { Player } from '../api/sleeper';
import { playerName } from '../api/sleeper';
import { injuryFlag } from '../lib/scoring';
import { colors, font, spacing } from '../theme';
import { PositionBadge } from './ui';

const INJURY_COLOR: Record<number, string> = {
  1: colors.textFaint,
  2: colors.amber,
  3: colors.red,
  4: colors.red,
};

export function PlayerRow({
  id,
  player,
  slot,
  points,
  pointsLabel,
  subdued,
  highlight,
}: {
  id: string;
  player: Player | undefined;
  slot?: string;
  points?: number;
  pointsLabel?: string;
  subdued?: boolean;
  highlight?: boolean;
}) {
  const injury = injuryFlag(player);
  const team = player?.team || 'FA';
  const pos = player?.position || player?.fantasy_positions?.[0] || null;

  return (
    <View style={[styles.row, highlight && styles.highlight]}>
      {slot ? (
        <View style={styles.slot}>
          <Text style={styles.slotText}>{slot}</Text>
        </View>
      ) : null}
      <PositionBadge pos={pos} />
      <View style={{ flex: 1 }}>
        <Text style={[styles.name, subdued && { color: colors.textDim }]} numberOfLines={1}>
          {playerName(player, id)}
        </Text>
        <View style={styles.metaRow}>
          <Text style={styles.meta}>{team}</Text>
          {injury ? (
            <Text style={[styles.injury, { color: INJURY_COLOR[injury.severity] || colors.amber }]}>
              {' · '}
              {injury.label}
            </Text>
          ) : null}
        </View>
      </View>
      {points !== undefined ? (
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={styles.points}>{points.toFixed(1)}</Text>
          {pointsLabel ? <Text style={styles.pointsLabel}>{pointsLabel}</Text> : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
  highlight: {
    backgroundColor: colors.cardAlt,
    borderRadius: 10,
    paddingHorizontal: spacing.sm,
  },
  slot: {
    width: 34,
    alignItems: 'center',
  },
  slotText: { color: colors.textFaint, fontSize: font.tiny, fontWeight: '800' },
  name: { color: colors.text, fontSize: font.body, fontWeight: '600' },
  metaRow: { flexDirection: 'row', alignItems: 'center', marginTop: 1 },
  meta: { color: colors.textFaint, fontSize: font.tiny },
  injury: { fontSize: font.tiny, fontWeight: '700' },
  points: { color: colors.text, fontSize: font.h3, fontWeight: '800' },
  pointsLabel: { color: colors.textFaint, fontSize: font.tiny, textTransform: 'uppercase' },
});
