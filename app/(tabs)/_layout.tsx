import { Ionicons } from '@expo/vector-icons';
import { Redirect, Tabs } from 'expo-router';
import { useApp } from '../../src/store/AppContext';
import { colors } from '../../src/theme';

export default function TabsLayout() {
  const { ready, user, leagueId } = useApp();
  if (ready && (!user || !leagueId)) return <Redirect href="/setup" />;

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerTintColor: colors.text,
        headerShadowVisible: false,
        headerTitleStyle: { fontWeight: '800' },
        tabBarStyle: {
          backgroundColor: colors.bgElevated,
          borderTopColor: colors.border,
        },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textFaint,
      }}
      sceneContainerStyle={{ backgroundColor: colors.bg }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'News Room',
          headerShown: false,
          tabBarIcon: ({ color, size }) => <Ionicons name="newspaper" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="trade"
        options={{
          title: 'Trade',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="swap-horizontal" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="draft"
        options={{
          title: 'Draft',
          tabBarIcon: ({ color, size }) => <Ionicons name="list" color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
