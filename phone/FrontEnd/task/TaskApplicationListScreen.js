import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator,TouchableOpacity } from 'react-native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Toast from 'react-native-toast-message';
import { useRoute } from '@react-navigation/native';

import { BASE_URL } from '../config';
import { TYPOGRAPHY, COLORS } from '../styles/theme';

export default function TaskApplicationListScreen() {
  const route = useRoute();
  const { taskId } = route.params;

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchApplications = async () => {
    try {
      console.log('正在获取申请人员名单......');
      const token = await AsyncStorage.getItem('userToken');
      const res = await axios.get(`${BASE_URL}/mobile/task/${taskId}/applications/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setApplications(res.data.applications || []);
    } catch (error) {
      console.error('❌ 获取申请失败:', error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const renderItem = ({ item }) => {
    const volunteer = item.volunteer || {};
    return (
      <View style={styles.card}>
        <Text style={styles.name}>{volunteer.full_name || 'Unnamed Volunteer'}</Text>
        <Text style={styles.email}>{volunteer.email}</Text>
        <Text style={styles.status}>Status: {item.status}</Text>
        {item.is_auto_matched && <Text style={styles.auto}>自动匹配</Text>}

        {item.status === 'pending' && (
          <View style={styles.actionRow}>
            <TouchableOpacity onPress={() => handleApprove(item.id)} style={styles.approveButton}>
              <Text style={styles.buttonText}>Approve</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleReject(item.id)} style={styles.rejectButton}>
              <Text style={styles.rejectText}>Reject</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
      
    );
  };

  const handleApprove = async (applicationId) => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    await axios.post(`${BASE_URL}/mobile/task/${taskId}/applications/${applicationId}/approve/`, {}, {
      headers: { Authorization: `Token ${token}` },
    });
    Toast.show({
      type: 'success',
      text1: 'Success',
      text2: 'Application approved!',
    });
    fetchApplications(); // 重新加载列表
  } catch (err) {
    console.error('Approve failed:', err);
  }
};

const handleReject = async (applicationId) => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    await axios.post(`${BASE_URL}/mobile/task/${taskId}/applications/${applicationId}/reject/`, {}, {
      headers: { Authorization: `Token ${token}` },
    });
    Toast.show({
      type: 'success',
      text1: 'Success',
      text2: 'Application rejected.',
    });
    fetchApplications();
  } catch (err) {
    console.error('Reject failed:', err);
  }
};

  return (
    <View style={styles.container}>
      <Text style={TYPOGRAPHY.title}>Applications</Text>

      {loading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 20 }} />
      ) : applications.length === 0 ? (
        <Text style={styles.noData}>No volunteers have applied for this task.</Text>
      ) : (
        <FlatList
          data={applications}
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
  name: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  email: {
    marginTop: 4,
    color: '#555',
  },
  status: {
    marginTop: 4,
    fontStyle: 'italic',
    color: COLORS.text,
  },
  auto: {
    marginTop: 2,
    color: '#888',
    fontSize: 12,
  },
  noData: {
    marginTop: 20,
    color: '#888',
    fontStyle: 'italic',
  },
  actionRow: {
  flexDirection: 'row',
  justifyContent: 'space-between',
  marginTop: 10,
  },
  approveButton: {
    flex: 1.2,
    backgroundColor: COLORS.primary,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  rejectButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e63946',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  rejectText: {
    color: '#e63946',
    fontWeight: 'bold',
  },
});
