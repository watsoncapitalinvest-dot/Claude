import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  getMatchups,
  getWeeklyProjections,
  getWeeklyStats,
  type Matchup,
} from '../../src/api/sleeper';
import { Avatar, Card, EmptyState, Loading } from '../../src/components/ui';
import { WeekStepper } from '../../src/components/WeekStepper';
import { useLeague } from '../../src/hooks/useLeague';
import { buildNewsletter, type GameStory, type Newsletter } from '../../src/lib/narrative';
import { useApp } from '../../src/store/AppContext';
import { colors, font, radius, spacing } from '../../src/theme';

export default function NewsRoom() {
  const router = useRouter();
  const { data, loading: leagueLoading, error, refresh } = useLeague();
  const { season, activeWeek, setActiveWeek, nflState } = useApp();

  const [matchups, setMatchups] = useState<Matchup[] | null>(null);
  const [stats, setStats] = useState<Record<string, Record<string, number>>>({});
  const [proj, setProj] = useState<Record<string, Record<string, number>>>({});
  const [busy, setBusy] = useState(false);

  const leagueId = data?.league.league_id;

  useEffect(() => {
    if (!leagueId || !season) return;
    let cancelled = false;
    setBusy(true);
    Promise.all([
      getMatchups(leagueId, activeWeek),
      getWeeklyStats(season, activeWeek),
      getWeeklyProjections(season, activeWeek),
    ])
      .then(([m, s, p]) => {
        if (cancelled) return;
        setMatchups(m);
        setStats(s);
        setProj(p);
      })
      .catch(() => {
        if (!cancelled) setMatchups([]);
      })
      .finally(() => !cancelled && setBusy(false));
    return () => {
      cancelled = true;
    };
  }, [leagueId, season, activeWeek]);

  const newsletter = useMemo<Newsletter | null>(() => {
    if (!data || !matchups) return null;
    return buildNewsletter({
      week: activeWeek,
      league: data.league,
      matchups,
      rosters: data.rosters,
      usersById: data.usersById,
      players: data.players,
      weeklyStats: stats,
      weeklyProjections: proj,
    });
  }, [data, matchups, stats, proj, activeWeek]);

  if (leagueLoading && !data) return <Loading label="Opening the news room…" />;
  if (error) return <EmptyState title="Couldn't load league" subtitle={error} />;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.bg }}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={leagueLoading} onRefresh={refresh} tintColor={colors.accent} />
      }
    >
      {/* Masthead */}
      <View style={styles.masthead}>
        <View style={{ flex: 1 }}>
          <Text style={styles.mastheadKicker}>THE GRIDIRON GAZETTE</Text>
          <Text style={styles.mastheadLeague} numberOfLines={1}>
            {data?.league.name ?? 'Your League'}
          </Text>
        </View>
        <Ionicons
          name="settings-outline"
          size={22}
          color={colors.textFaint}
          onPress={() => router.push('/settings')}
        />
      </View>

      <WeekStepper
        week={activeWeek}
        onChange={setActiveWeek}
        currentWeek={nflState?.display_week || nflState?.week}
      />

      {busy && !newsletter ? (
        <Loading label={`Writing the Week ${activeWeek} edition…`} />
      ) : !newsletter || !newsletter.hasData ? (
        <EmptyState
          title={`No games scored for Week ${activeWeek} yet`}
          subtitle="Once the games kick off, your newsletter writes itself. Try an earlier week."
        />
      ) : (
        <>
          {/* Lead article */}
          <View style={styles.lead}>
            <Text style={styles.leadHeadline}>{newsletter.lead.headline}</Text>
            <Text style={styles.standfirst}>{newsletter.lead.standfirst}</Text>
            {newsletter.lead.paragraphs.map((p, i) => (
              <Text key={i} style={styles.body}>
                {p}
              </Text>
            ))}
          </View>

          {/* Awards */}
          {newsletter.awards.length > 0 ? (
            <Card style={styles.awardsCard}>
              <Text style={styles.awardsTitle}>Week {activeWeek} Superlatives</Text>
              {newsletter.awards.map((a, i) => (
                <View key={i} style={styles.awardRow}>
                  <Text style={styles.awardEmoji}>{a.emoji}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.awardLabel}>{a.title}</Text>
                    <Text style={styles.awardName}>{a.name}</Text>
                    <Text style={styles.awardDetail}>{a.detail}</Text>
                  </View>
                </View>
              ))}
            </Card>
          ) : null}

          {/* Game stories */}
          <Text style={styles.sectionRule}>GAME STORIES</Text>
          {newsletter.stories.map((s) => (
            <GameStoryCard key={s.id} story={s} />
          ))}

          <Text style={styles.colophon}>
            Auto-written from live Sleeper box scores — real stat lines, real fantasy margins. Refreshed
            every time you open the app.
          </Text>
        </>
      )}
    </ScrollView>
  );
}

function GameStoryCard({ story }: { story: GameStory }) {
  return (
    <Card style={styles.story}>
      <View style={styles.storyScoreline}>
        <TeamTag name={story.winner.manager} avatar={story.winner.avatar} score={story.winner.score} win />
        <Text style={styles.dash}>–</Text>
        <TeamTag name={story.loser.manager} avatar={story.loser.avatar} score={story.loser.score} alignRight />
      </View>
      <Text style={styles.storyHeadline}>{story.headline}</Text>
      <Text style={styles.dek}>{story.dek}</Text>
      {story.paragraphs.map((p, i) => (
        <Text key={i} style={styles.body}>
          {p}
        </Text>
      ))}
    </Card>
  );
}

function TeamTag({
  name,
  avatar,
  score,
  win,
  alignRight,
}: {
  name: string;
  avatar: string | null;
  score: number;
  win?: boolean;
  alignRight?: boolean;
}) {
  return (
    <View
      style={[
        styles.teamTag,
        { flexDirection: alignRight ? 'row-reverse' : 'row', justifyContent: alignRight ? 'flex-start' : 'flex-start' },
      ]}
    >
      <Avatar uri={avatar} size={28} fallback={name} />
      <View style={{ alignItems: alignRight ? 'flex-end' : 'flex-start' }}>
        <Text style={[styles.teamTagName, win && { color: colors.accent }]} numberOfLines={1}>
          {name}
        </Text>
        <Text style={[styles.teamTagScore, win && { color: colors.accent }]}>{score.toFixed(1)}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  masthead: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: colors.text,
    paddingBottom: spacing.sm,
  },
  mastheadKicker: { color: colors.accent, fontSize: font.tiny, fontWeight: '900', letterSpacing: 2 },
  mastheadLeague: { color: colors.text, fontSize: font.h1, fontWeight: '900', fontStyle: 'italic' },
  lead: { gap: spacing.sm },
  leadHeadline: { color: colors.text, fontSize: 28, fontWeight: '900', lineHeight: 32 },
  standfirst: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  body: { color: colors.textDim, fontSize: font.body, lineHeight: 23 },
  awardsCard: { gap: spacing.md, borderColor: colors.accentDim },
  awardsTitle: {
    color: colors.text,
    fontSize: font.h3,
    fontWeight: '800',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    paddingBottom: spacing.sm,
  },
  awardRow: { flexDirection: 'row', gap: spacing.md, alignItems: 'center' },
  awardEmoji: { fontSize: 26 },
  awardLabel: {
    color: colors.textFaint,
    fontSize: font.tiny,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  awardName: { color: colors.text, fontSize: font.body, fontWeight: '800' },
  awardDetail: { color: colors.textDim, fontSize: font.small },
  sectionRule: {
    color: colors.text,
    fontSize: font.tiny,
    fontWeight: '900',
    letterSpacing: 2,
    textAlign: 'center',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingVertical: spacing.sm,
  },
  story: { gap: spacing.sm },
  storyScoreline: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingBottom: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  teamTag: { flex: 1, alignItems: 'center', gap: spacing.sm },
  teamTagName: { color: colors.textDim, fontSize: font.small, fontWeight: '700', maxWidth: 110 },
  teamTagScore: { color: colors.text, fontSize: font.h3, fontWeight: '900' },
  dash: { color: colors.textFaint, fontSize: font.h3, fontWeight: '700' },
  storyHeadline: { color: colors.text, fontSize: font.h2, fontWeight: '900', lineHeight: 26 },
  dek: { color: colors.blue, fontSize: font.small, fontWeight: '700', fontStyle: 'italic' },
  colophon: {
    color: colors.textFaint,
    fontSize: font.tiny,
    textAlign: 'center',
    lineHeight: 16,
    marginTop: spacing.sm,
  },
});
