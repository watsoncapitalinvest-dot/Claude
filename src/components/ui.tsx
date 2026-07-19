/** Small, dependency-free UI primitives shared across screens. */
import React from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { colors, font, positionColors, radius, spacing } from '../theme';

export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function SectionHeader({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {right}
    </View>
  );
}

export function PositionBadge({ pos }: { pos: string | null | undefined }) {
  const p = pos || '—';
  const color = positionColors[p] || colors.textFaint;
  return (
    <View style={[styles.posBadge, { borderColor: color }]}>
      <Text style={[styles.posText, { color }]}>{p}</Text>
    </View>
  );
}

export function Avatar({
  uri,
  size = 36,
  fallback,
}: {
  uri: string | null;
  size?: number;
  fallback?: string;
}) {
  const [failed, setFailed] = React.useState(false);
  if (uri && !failed) {
    return (
      <Image
        source={{ uri }}
        onError={() => setFailed(true)}
        style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: colors.cardAlt }}
      />
    );
  }
  const letter = (fallback || '?').trim().charAt(0).toUpperCase();
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: colors.cardAlt,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Text style={{ color: colors.textDim, fontWeight: '700', fontSize: size * 0.42 }}>
        {letter}
      </Text>
    </View>
  );
}

export function Pill({
  label,
  color = colors.textDim,
  bg,
}: {
  label: string;
  color?: string;
  bg?: string;
}) {
  return (
    <View style={[styles.pill, { backgroundColor: bg || 'transparent', borderColor: color }]}>
      <Text style={[styles.pillText, { color }]}>{label}</Text>
    </View>
  );
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  disabled,
}: {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'ghost' | 'danger';
  disabled?: boolean;
}) {
  const bg =
    variant === 'primary' ? colors.accent : variant === 'danger' ? 'transparent' : 'transparent';
  const border =
    variant === 'primary' ? colors.accent : variant === 'danger' ? colors.red : colors.border;
  const fg =
    variant === 'primary' ? '#04210d' : variant === 'danger' ? colors.red : colors.text;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, borderColor: border, opacity: disabled ? 0.4 : pressed ? 0.8 : 1 },
      ]}
    >
      <Text style={[styles.buttonText, { color: fg }]}>{label}</Text>
    </Pressable>
  );
}

export function Loading({ label }: { label?: string }) {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={colors.accent} />
      {label ? <Text style={styles.dim}>{label}</Text> : null}
    </View>
  );
}

export function EmptyState({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={styles.center}>
      <Text style={styles.emptyTitle}>{title}</Text>
      {subtitle ? <Text style={styles.dim}>{subtitle}</Text> : null}
    </View>
  );
}

export function StatBox({ label, value, tint }: { label: string; value: string; tint?: string }) {
  return (
    <View style={styles.statBox}>
      <Text style={[styles.statValue, tint ? { color: tint } : null]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
    marginTop: spacing.sm,
  },
  sectionTitle: { color: colors.text, fontSize: font.h3, fontWeight: '700' },
  posBadge: {
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
    minWidth: 34,
    alignItems: 'center',
  },
  posText: { fontSize: font.tiny, fontWeight: '800', letterSpacing: 0.5 },
  pill: {
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  pillText: { fontSize: font.tiny, fontWeight: '700' },
  button: {
    borderWidth: 1,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    alignItems: 'center',
  },
  buttonText: { fontSize: font.body, fontWeight: '700' },
  center: { alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.sm },
  dim: { color: colors.textDim, fontSize: font.small, textAlign: 'center' },
  emptyTitle: { color: colors.text, fontSize: font.h3, fontWeight: '700', textAlign: 'center' },
  statBox: { flex: 1, alignItems: 'center', paddingVertical: spacing.sm },
  statValue: { color: colors.text, fontSize: font.h2, fontWeight: '800' },
  statLabel: { color: colors.textFaint, fontSize: font.tiny, marginTop: 2, textTransform: 'uppercase' },
});
