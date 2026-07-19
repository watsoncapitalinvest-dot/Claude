import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  avatarUrl,
  getNflState,
  getUser,
  getUserLeagues,
  type League,
  type SleeperUser,
} from '../src/api/sleeper';
import { useApp } from '../src/store/AppContext';
import { Avatar, Button, Card, Loading } from '../src/components/ui';
import { colors, font, radius, spacing } from '../src/theme';

export default function Setup() {
  const router = useRouter();
  const { signIn } = useApp();
  const [username, setUsername] = useState('');
  const [user, setUser] = useState<SleeperUser | null>(null);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [season, setSeason] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const insets = useSafeAreaInsets();

  async function lookup() {
    const name = username.trim();
    if (!name) return;
    setBusy(true);
    setError(null);
    setLeagues([]);
    setUser(null);
    try {
      const state = await getNflState();
      const ssn = state.season || String(new Date().getFullYear());
      const u = await getUser(name);
      if (!u || !u.user_id) {
        setError(`No Sleeper user found for "${name}".`);
        return;
      }
      setUser(u);
      setSeason(ssn);
      let ls = await getUserLeagues(u.user_id, ssn);
      // Off-season: this year's leagues may not exist yet — fall back a year.
      if ((!ls || ls.length === 0) && Number(ssn) > 2020) {
        const prev = String(Number(ssn) - 1);
        ls = await getUserLeagues(u.user_id, prev);
        if (ls && ls.length) setSeason(prev);
      }
      setLeagues(ls || []);
      if (!ls || ls.length === 0) {
        setError('That user has no NFL leagues on Sleeper for this season.');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Check your connection.');
    } finally {
      setBusy(false);
    }
  }

  async function choose(league: League) {
    if (!user) return;
    setBusy(true);
    try {
      await signIn(user, league.league_id, league.season || season);
      router.replace('/(tabs)');
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: colors.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={{
          padding: spacing.lg,
          paddingTop: insets.top + spacing.xl,
          paddingBottom: insets.bottom + spacing.xl,
          gap: spacing.lg,
        }}
        keyboardShouldPersistTaps="handled"
      >
        <View style={{ gap: spacing.xs }}>
          <Text style={styles.logo}>🏈 Gridiron GM</Text>
          <Text style={styles.tagline}>Your fantasy front office, powered by Sleeper.</Text>
        </View>

        <Card style={{ gap: spacing.md }}>
          <Text style={styles.label}>Sleeper username</Text>
          <TextInput
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="e.g. yourhandle"
            placeholderTextColor={colors.textFaint}
            style={styles.input}
            returnKeyType="search"
            onSubmitEditing={lookup}
          />
          <Button label={busy && !user ? 'Looking up…' : 'Find my leagues'} onPress={lookup} disabled={busy} />
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </Card>

        {busy && !user ? <Loading /> : null}

        {user && leagues.length > 0 ? (
          <View style={{ gap: spacing.sm }}>
            <Text style={styles.sectionLabel}>
              {season} leagues for {user.display_name}
            </Text>
            {leagues.map((lg) => (
              <Pressable key={lg.league_id} onPress={() => choose(lg)} disabled={busy}>
                <Card style={styles.leagueRow}>
                  <Avatar uri={avatarUrl(lg.avatar)} size={44} fallback={lg.name} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.leagueName}>{lg.name}</Text>
                    <Text style={styles.leagueMeta}>
                      {lg.total_rosters}-team · {scoringLabel(lg)} · {lg.status.replace('_', ' ')}
                    </Text>
                  </View>
                  <Text style={styles.chevron}>›</Text>
                </Card>
              </Pressable>
            ))}
          </View>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function scoringLabel(lg: League): string {
  const rec = lg.scoring_settings?.rec ?? 0;
  if (rec >= 1) return 'PPR';
  if (rec >= 0.5) return 'Half-PPR';
  return 'Standard';
}

const styles = StyleSheet.create({
  logo: { color: colors.text, fontSize: font.h1, fontWeight: '800' },
  tagline: { color: colors.textDim, fontSize: font.body },
  label: { color: colors.textDim, fontSize: font.small, fontWeight: '600' },
  sectionLabel: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginLeft: spacing.xs,
  },
  input: {
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    color: colors.text,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: font.body,
  },
  error: { color: colors.red, fontSize: font.small },
  leagueRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  leagueName: { color: colors.text, fontSize: font.h3, fontWeight: '700' },
  leagueMeta: { color: colors.textDim, fontSize: font.small, marginTop: 2 },
  chevron: { color: colors.textFaint, fontSize: 28, fontWeight: '300' },
});
