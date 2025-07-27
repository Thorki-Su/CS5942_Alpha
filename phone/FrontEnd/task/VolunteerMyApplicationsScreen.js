import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity,
} from 'react-native';
import { useNavigation,useFocusEffect } from '@react-navigation/native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { format } from 'date-fns';
import { BASE_URL } from '../config';
import { COLORS, TYPOGRAPHY } from '../styles/theme';

export default function VolunteerMyApplicationsScreen() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  const navigation = useNavigation();

  useFocusEffect(
    React.useCallback(() => {
        fetchApplications();
    }, [])
    );

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('userToken');
      const res = await axios.get(`${BASE_URL}/mobile/task/volunteer/applications/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setApplications(res.data.applications || []);
    } catch (err) {
      console.error('Error fetching applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const filteredApplications = applications.filter((app) => {
    if (activeTab === 'pending') {
      return app.status === 'pending';
    }
    if (activeTab === 'ongoing') {
      return app.status === 'accepted' && app.task_status === 'ongoing';
    }
    if (activeTab === 'finished') {
      return (
        app.status === 'rejected' ||
        app.task_status === 'cancelled' ||
        app.task_status === 'completed' || // ✅ 补上 completed 任务
        (app.status === 'accepted' && app.task_status === 'finished')
      );
    }
    return false;
  });

  const tabOptions = [
    { key: 'pending', label: 'Pending' },
    { key: 'ongoing', label: 'Ongoing' },
    { key: 'finished', label: 'Finished' },
  ];

  const renderItem = ({ item }) => (
    <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('VolunteerApplicationDetail', {
        application: item,
        })}
    >
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.time}>
        Time: {format(new Date(item.start_time), 'EEEE, d MMMM yyyy · hh:mm a')} →{' '}
        {format(new Date(item.end_time), 'EEEE, d MMMM yyyy · hh:mm a')}
      </Text>
      <Text style={styles.status}>Application Status: {item.status}</Text>
      {/* <Text style={styles.status}>Task Status: {item.task_status}</Text> */}
      <Text style={styles.appliedAt}>
        Applied at: {format(new Date(item.applied_at), 'EEEE, d MMMM yyyy · hh:mm a')}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={TYPOGRAPHY.title}>My Applications</Text>

      <View style={styles.tabRow}>
        {tabOptions.map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            style={[
              styles.tabButton,
              activeTab === key && styles.activeTabButton,
            ]}
            onPress={() => setActiveTab(key)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === key && styles.activeTabText,
              ]}
            >
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 20 }} />
      ) : filteredApplications.length === 0 ? (
        <Text style={styles.noData}>No applications found.</Text>
      ) : (
        <FlatList
          data={filteredApplications}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
    flex: 1,
  },
  card: {
    backgroundColor: '#fff',
    padding: 14,
    marginTop: 12,
    borderRadius: 8,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  time: {
    marginTop: 4,
    color: '#555',
  },
  status: {
    marginTop: 4,
    color: '#333',
  },
  appliedAt: {
    marginTop: 4,
    fontStyle: 'italic',
    color: '#888',
  },
  noData: {
    marginTop: 20,
    color: '#888',
    fontStyle: 'italic',
  },
  tabRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 12,
  },
  tabButton: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  activeTabButton: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  tabText: {
    fontSize: 14,
    color: '#333',
  },
  activeTabText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
