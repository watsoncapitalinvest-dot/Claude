import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, font, radius, spacing } from '../theme';

const MAX_WEEK = 18;

export function WeekStepper({
  week,
  onChange,
  currentWeek,
}: {
  week: number;
  onChange: (w: number) => void;
  currentWeek?: number | null;
}) {
  const isNow = currentWeek != null && week === currentWeek;
  return (
    <View style={styles.wrap}>
      <Pressable
        onPress={() => onChange(Math.max(1, week - 1))}
        disabled={week <= 1}
        style={({ pressed }) => [styles.btn, { opacity: week <= 1 ? 0.3 : pressed ? 0.6 : 1 }]}
        hitSlop={8}
      >
        <Text style={styles.arrow}>‹</Text>
      </Pressable>
      <View style={styles.center}>
        <Text style={styles.week}>Week {week}</Text>
        {isNow ? <Text style={styles.live}>NOW</Text> : null}
      </View>
      <Pressable
        onPress={() => onChange(Math.min(MAX_WEEK, week + 1))}
        disabled={week >= MAX_WEEK}
        style={({ pressed }) => [
          styles.btn,
          { opacity: week >= MAX_WEEK ? 0.3 : pressed ? 0.6 : 1 },
        ]}
        hitSlop={8}
      >
        <Text style={styles.arrow}>›</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.bgElevated,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  btn: { paddingHorizontal: spacing.md, paddingVertical: 2 },
  arrow: { color: colors.text, fontSize: 24, fontWeight: '700' },
  center: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  week: { color: colors.text, fontSize: font.body, fontWeight: '800' },
  live: {
    color: colors.accent,
    fontSize: font.tiny,
    fontWeight: '900',
    borderWidth: 1,
    borderColor: colors.accentDim,
    borderRadius: radius.sm,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
});
