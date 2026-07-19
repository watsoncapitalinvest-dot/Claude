import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { avatarUrl, getNflState, getUserLeagues, type League } from '../src/api/sleeper';
import { Avatar, Button, Card, Loading } from '../src/components/ui';
import { useApp } from '../src/store/AppContext';
import { colors, font, spacing } from '../src/theme';

export default function Settings() {
  const router = useRouter();
  const { user, leagueId, season, switchLeague, signOut } = useApp();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const state = await getNflState().catch(() => null);
        const ssn = season || state?.season || String(new Date().getFullYear());
        let ls = await getUserLeagues(user.user_id, ssn);
        if ((!ls || ls.length === 0) && Number(ssn) > 2020) {
          ls = await getUserLeagues(user.user_id, String(Number(ssn) - 1));
        }
        if (!cancelled) setLeagues(ls || []);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, season]);

  async function onSwitch(lg: League) {
    await switchLeague(lg.league_id, lg.season || season || '');
    router.back();
  }

  async function onSignOut() {
    await signOut();
    router.replace('/setup');
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.bg }}
      contentContainerStyle={{ padding: spacing.lg, gap: spacing.lg }}
    >
      {user ? (
        <Card style={styles.userRow}>
          <Avatar uri={avatarUrl(user.avatar)} size={48} fallback={user.display_name} />
          <View>
            <Text style={styles.name}>{user.display_name}</Text>
            <Text style={styles.handle}>@{user.username}</Text>
          </View>
        </Card>
      ) : null}

      <Text style={styles.sectionLabel}>Your leagues</Text>
      {loading ? (
        <Loading />
      ) : (
        leagues.map((lg) => {
          const active = lg.league_id === leagueId;
          return (
            <Pressable key={lg.league_id} onPress={() => onSwitch(lg)}>
              <Card style={[styles.leagueRow, active && { borderColor: colors.accent }]}>
                <Avatar uri={avatarUrl(lg.avatar)} size={40} fallback={lg.name} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.leagueName}>{lg.name}</Text>
                  <Text style={styles.leagueMeta}>
                    {lg.season} · {lg.total_rosters}-team
                  </Text>
                </View>
                {active ? <Text style={styles.activeTag}>ACTIVE</Text> : null}
              </Card>
            </Pressable>
          );
        })
      )}

      <View style={{ marginTop: spacing.lg }}>
        <Button label="Sign out" onPress={onSignOut} variant="danger" />
      </View>
      <Text style={styles.footnote}>Gridiron GM · a companion to Sleeper · not affiliated with Sleeper.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  userRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  name: { color: colors.text, fontSize: font.h3, fontWeight: '800' },
  handle: { color: colors.textDim, fontSize: font.small },
  sectionLabel: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  leagueRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  leagueName: { color: colors.text, fontSize: font.body, fontWeight: '700' },
  leagueMeta: { color: colors.textDim, fontSize: font.small },
  activeTag: { color: colors.accent, fontSize: font.tiny, fontWeight: '900' },
  footnote: { color: colors.textFaint, fontSize: font.tiny, textAlign: 'center', marginTop: spacing.md },
});
