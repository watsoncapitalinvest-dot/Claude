import { Redirect } from 'expo-router';
import { View } from 'react-native';
import { useApp } from '../src/store/AppContext';
import { Loading } from '../src/components/ui';
import { colors } from '../src/theme';

/** Boot gate: wait for persisted session, then route to setup or the app. */
export default function Index() {
  const { ready, user, leagueId } = useApp();

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg, justifyContent: 'center' }}>
        <Loading label="Loading Gridiron GM…" />
      </View>
    );
  }

  if (user && leagueId) return <Redirect href="/(tabs)" />;
  return <Redirect href="/setup" />;
}
