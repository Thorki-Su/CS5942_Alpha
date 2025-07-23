import React, { useEffect, useState,useCallback } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  Alert,
  StyleSheet,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation,useFocusEffect } from '@react-navigation/native';
import { COLORS, TYPOGRAPHY, BUTTON_STYLE } from '../../styles/theme';
import { BASE_URL } from '../../config';
import DefaultAvatar from '../../assets/default_avatar.png';

import { fetchUserProfile } from '../../components/fetchUserProfile';

export default function ProfileDetailScreen() {
  const [profile, setProfile] = useState(null);
  const navigation = useNavigation();

  useFocusEffect(
    useCallback(() => {
      const refresh = async () => {
        const data = await fetchUserProfile();
        if (data) {
          setProfile(data);
          console.log('🌀 useFocusEffect: 已刷新 profile 数据');
        }
      };
      refresh();
    }, [])
  );

  const handleLogout = async () => {
    Alert.alert(
      'Confirm Logout',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('loggedInEmail');
            await AsyncStorage.removeItem('userToken');
            await AsyncStorage.removeItem('userData');
            await AsyncStorage.clear();
            console.log('🧼 Storage cleared.');
            navigation.reset({
              index: 0,
              routes: [{ name: 'Login' }],
            });
          },
        },
      ]
    );
  };


  if (!profile) return <Text style={styles.loading}>Loading profile...</Text>;

  const { user, user_profile, client_fields, volunteer_fields } = profile;

  const renderFields = (fields) => {
    const skipKeys = ['id', 
      'user', 
      'user_profile', 
      'profile_photo', 
      'availability', 
      'available_days', 
      'available_start_time', 
      'available_end_time'];

  return Object.entries(fields).map(([key, value]) => {
    if (skipKeys.includes(key)) return null;

    let displayValue = '';

    if (value === null || value === undefined) {
      displayValue = '(Unfilled)';
    } else if (Array.isArray(value)) {
      displayValue = value.length > 0 ? value.join(', ') : '(Unfilled)';
    } else if (typeof value === 'object') {
      displayValue = JSON.stringify(value);
    } else {
      displayValue = value.toString();
    }

    return (
      <Text key={key} style={styles.field}>
        <Text style={styles.label}>{key}:</Text> {displayValue}
      </Text>
    );
  });
};

  return (
  <ScrollView style={styles.container}>
    <Text style={TYPOGRAPHY.title}>Hello, {profile.user_profile?.first_name || '(No Name)'}</Text>
    <Text style={styles.subtitle}>Thanks for using Shallion as a {profile.user?.role || 'user'}!</Text>

    <TouchableOpacity
      onPress={() => navigation.navigate('UploadAvatarScreen')}
      activeOpacity={0.8}
    >
      <View style={styles.avatarContainer}>
        <Image
          source={user_profile.profile_photo ? { uri: user_profile.profile_photo } : DefaultAvatar}
          style={styles.avatarImage}
        />
      </View>
    </TouchableOpacity>

    <Text style={styles.section}>Basic Info</Text>
    <Text style={styles.field}>
      <Text style={styles.label}>Email:</Text> {profile.user?.email || '(No Email)'}
    </Text>
    {renderFields(profile.user_profile || {})}

    <Text style={styles.section}>Additional Info</Text>
    {/* <Text style={{ color: 'red' }}>🔥 client fields start</Text> */}
    {profile.user?.role === 'client' && renderFields(profile.client_fields || {})}
    {/* <Text style={{ color: 'red' }}>🔥 client fields end</Text> */}
    {profile.user?.role === 'volunteer' && renderFields(profile.volunteer_fields || {})}

    <View style={styles.buttonGroup}>
      <TouchableOpacity
        style={BUTTON_STYLE}
        onPress={() => navigation.navigate(
          profile.user?.role === 'client' ? 'EditClientProfile' : 'EditVolunteerProfile'
        )}
      >
        <Text style={TYPOGRAPHY.buttonText}>Edit Information</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={BUTTON_STYLE}
        onPress={() => navigation.navigate('ChangePassword')}
      >
        <Text style={TYPOGRAPHY.buttonText}>Change Password</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[BUTTON_STYLE, { backgroundColor: '#ccc' }]}
        onPress={handleLogout}
      >
        <Text style={[TYPOGRAPHY.buttonText, { color: '#000' }]}>Log Out</Text>
      </TouchableOpacity>
    </View>
  </ScrollView>
);
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: COLORS.background,
  },
  loading: {
    marginTop: 50,
    textAlign: 'center',
    fontSize: 16,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 20,
    color: COLORS.text,
  },
  section: {
    marginTop: 20,
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  field: {
    marginTop: 8,
    fontSize: 16,
    color: COLORS.text,
  },
  label: {
    fontWeight: 'bold',
  },
  avatar: {
    width: 120,
    height: 120,
    borderRadius: 60,
    marginTop: 10,
    marginBottom: 20,
  },
  buttonGroup: {
    marginTop: 30,
    gap: 12,
  },
  avatarContainer: {
  width: 140,
  height: 140,
  borderRadius: 70,
  backgroundColor: '#eee',
  justifyContent: 'center',
  alignItems: 'center',
  alignSelf: 'center',
  marginBottom: 20,
  },
  avatarImage: {
    width: 140,
    height: 140,
    borderRadius: 70,
    resizeMode: 'cover',
  },
});
