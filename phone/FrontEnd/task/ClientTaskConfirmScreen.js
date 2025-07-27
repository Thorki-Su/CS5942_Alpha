import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ActivityIndicator, Alert, TouchableOpacity, ScrollView,
} from 'react-native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BASE_URL } from '../config';
import { COLORS, TYPOGRAPHY } from '../styles/theme';
import { useNavigation, useRoute } from '@react-navigation/native';

export default function ClientTaskConfirmScreen() {
  const [recordData, setRecordData] = useState(null);
  const [loading, setLoading] = useState(true);
  const route = useRoute();
  const navigation = useNavigation();
  const { taskId } = route.params;
	console.log('📥 Received taskId:', taskId)

  useEffect(() => {
    fetchRecord();
  }, []);

  const fetchRecord = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const res = await axios.get(`${BASE_URL}/mobile/task/${taskId}/record/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setRecordData(res.data);
    } catch (err) {
      console.error('Error fetching record:', err.response?.data || err.message);
      Alert.alert('Error', 'Unable to fetch task record.');
    } finally {
      setLoading(false);
    }
  };

  const confirmTask = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      await axios.post(`${BASE_URL}/mobile/task/${taskId}/confirm/`, {}, {
        headers: { Authorization: `Token ${token}` },
      });
      Alert.alert('Success', 'Task confirmed and marked as completed.');
      navigation.goBack();
    } catch (err) {
      console.error('Error confirming task:', err.response?.data || err.message);
      Alert.alert('Error', 'Failed to confirm task.');
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!recordData) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>No record available for this task.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={TYPOGRAPHY.title}>Confirm Task Completion</Text>

      <Text style={styles.label}>Volunteer: {recordData.volunteer_name}</Text>
      <Text style={styles.label}>Submitted At: {recordData.submitted_at}</Text>

      <Text style={styles.sectionTitle}>Task Records:</Text>
      {recordData.records.map((item, index) => (
        <Text key={index} style={styles.recordItem}>• {item}</Text>
      ))}

      <TouchableOpacity style={styles.confirmButton} onPress={confirmTask}>
        <Text style={styles.confirmText}>✅ Confirm Task</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: 'red',
    fontSize: 16,
  },
  label: {
    fontSize: 16,
    marginBottom: 8,
    color: COLORS.text,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  recordItem: {
    fontSize: 16,
    marginBottom: 6,
    paddingLeft: 10,
    color: '#444',
  },
  confirmButton: {
    marginTop: 24,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  confirmText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
