// task/TaskDetailScreen.js
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
  Alert,
  Button,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { BASE_URL } from '../config';
import { COLORS } from '../styles/theme';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { differenceInHours, parseISO, format } from 'date-fns';

export default function TaskDetailScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { taskId } = route.params;

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [role, setRole] = useState(null);
  const [canCancel, setCanCancel] = useState(false);

  useEffect(() => {
    const fetchTask = async () => {
      const token = await AsyncStorage.getItem('userToken');
      try {
        const res = await axios.get(`${BASE_URL}/mobile/task/${taskId}/`, {
          headers: { Authorization: `Token ${token}` },
        });
        console.log("🧩 Task Status:", res.data.status, "Confirmed:", res.data.confirmed_by_client);
        setTask(res.data);
      } catch (err) {
        console.error('❌ 获取任务详情失败:', err);
        console.log('📩 错误响应：', err.response?.data);
      } finally {
        setLoading(false);
      }
    };
    fetchTask();
  }, [taskId]);

  useEffect(() => {
    if (task) {
      const now = new Date();
      const startTime = parseISO(task.start_time);
      const hoursUntilStart = differenceInHours(startTime, now);
      if (hoursUntilStart >= 24) {
        setCanCancel(true);
      }
    }
  }, [task]);

  useEffect(() => {
    const fetchUserRole = async () => {
      try {
        const token = await AsyncStorage.getItem('userToken');
        const res = await axios.get(`${BASE_URL}/api/mobile/profile/`, {
          headers: { Authorization: `Token ${token}` },
        });
        setRole(res.data.role);
      } catch (error) {
        console.error('获取用户角色失败:', error.response?.data || error.message);
      }
    };
    fetchUserRole();
  }, []);

  const handleCancelTask = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      await axios.post(`${BASE_URL}/mobile/task/${task.id}/cancel/`, {}, {
        headers: { Authorization: `Token ${token}` },
      });
      Alert.alert('Success', 'Task has been cancelled.');
      navigation.navigate('ClientTaskList');
    } catch (error) {
      Alert.alert('Error', 'Failed to cancel the task.');
    }
  };

  const handleForceCompleteTask = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const res = await axios.post(`${BASE_URL}/mobile/task/${task.id}/force-complete/`, {}, {
        headers: { Authorization: `Token ${token}` },
      });

      Alert.alert('Success', 'Task has been force-ended. Please wait for the volunteer to submit their record.');
      
      // 重新拉取任务状态（已更新 end_time）
      const refreshed = await axios.get(`${BASE_URL}/mobile/task/${task.id}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setTask(refreshed.data);

    } catch (error) {
      console.error('提前结束任务失败:', error.response?.data || error.message);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to end the task early.');
    }
  };

  const applyForTask = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      await axios.post(`${BASE_URL}/mobile/task/${task.id}/apply/`, {}, {
        headers: { Authorization: `Token ${token}` },
      });
      Alert.alert('Success', 'You have successfully applied for this task!');
    } catch (error) {
      Alert.alert('Error', 'Failed to apply for the task.');
    }
  };

  if (loading) return <ActivityIndicator style={{ marginTop: 100 }} />;
  if (!task) return <Text style={{ margin: 20 }}>无法加载任务详情</Text>;

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 300 }}>
        <Button
          title="进入视频通话"
          onPress={() => navigation.navigate('VideoCall', { taskId: task.id })}
        />
        <Text style={styles.title}>{task.title}</Text>
        <Text style={styles.label}>Description:</Text>
        <Text>{task.description}</Text>

        <Text style={styles.label}>Creator:</Text>
        <Text>{task.creator || 'Unknown'}</Text>

        <Text style={styles.label}>Time:</Text>
        <Text>
          {format(parseISO(task.start_time), "EEEE, d MMMM yyyy · hh:mm a")} - {format(parseISO(task.end_time), "hh:mm a")}
        </Text>

        <Text style={styles.label}>Support Needed:</Text>
        <Text>{task.work_area.join(', ')}</Text>

        <Text style={styles.label}>Volunteers Needed:</Text>
        <Text>{task.vol_number}</Text>

        <Text style={styles.label}>Status:</Text>
        <Text>{task.status}</Text>

        <Text style={styles.label}>Created At:</Text>
        <Text>{format(parseISO(task.created_at), "EEEE, d MMMM yyyy · hh:mm a")}</Text>

        {task.closed_at && (
          <>
            <Text style={styles.label}>Closed At:</Text>
            <Text>{task.closed_at}</Text>
          </>
        )}

        {role === 'client' && (
          <View>
            <Text style={styles.label}>Feedback for Volunteers:</Text>
            {task.accepted_volunteers?.length > 0 ? (
              task.accepted_volunteers.map((v, idx) => (
                <TouchableOpacity
                  key={idx}
                  onPress={() => navigation.navigate('ClientSubmitFeedback', {
                    taskId: task.id,
                    volunteerId: v.id,
                  })}
                >
                  <Text style={styles.linkText}>
                    {v.name} {v.has_feedback ? '✅' : '📝'}
                  </Text>
                </TouchableOpacity>
              ))
            ) : (
              <Text>No volunteers accepted yet.</Text>
            )}
          </View>
        )}
      </ScrollView>

      {/* 🟦 Client 操作区 */}
      {role === 'client' && (
        <View style={styles.bottomActions}>
          {task.status === 'open' && (
            <>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => navigation.navigate('TaskApplications', { taskId: task.id })}
              >
                <Text style={styles.buttonText}>View Applied Volunteers</Text>
              </TouchableOpacity>
              {canCancel && (
                <TouchableOpacity
                  style={styles.dangerButton}
                  onPress={() => {
                    Alert.alert(
                      'Confirm Cancellation',
                      'Are you sure you want to cancel this task?',
                      [
                        { text: 'No', style: 'cancel' },
                        { text: 'Yes', onPress: handleCancelTask, style: 'destructive' },
                      ]
                    );
                  }}
                >
                  <Text style={styles.buttonText}>Cancel This Task</Text>
                </TouchableOpacity>
              )}
            </>
          )}

          {task.status === 'ongoing' && (
            <>
              {task.volunteer_submitted && (
                <TouchableOpacity
                  style={styles.confirmBtn}
                  onPress={() => navigation.navigate('ClientTaskConfirm', { taskId: task.id })}
                >
                  <Text style={styles.confirmText}>Confirm Task Completion</Text>
                </TouchableOpacity>
              )}
              {!task.confirmed_by_client && (
                <TouchableOpacity
                  style={styles.dangerButton}
                  onPress={() => {
                    Alert.alert(
                      'End Task Early',
                      'Are you sure you want to end this task early? It will be marked as completed.',
                      [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Confirm', onPress: handleForceCompleteTask },
                      ]
                    );
                  }}
                >
                  <Text style={styles.buttonText}>🚨 End Task Early</Text>
                </TouchableOpacity>
              )}
            </>
          )}
        </View>
      )}

      {/* 🟢 Volunteer 操作区 */}
      {role === 'volunteer' && (
        <TouchableOpacity style={styles.applyButton} onPress={applyForTask}>
          <Text style={styles.buttonText}>Apply for this Task</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  label: { marginTop: 12, fontWeight: '600' },
  secondaryButton: {
    backgroundColor: '#007bff',
    padding: 10,
    borderRadius: 6,
    marginTop: 12,
  },
  dangerButton: {
    backgroundColor: '#ff4d4d',
    padding: 10,
    borderRadius: 6,
    marginTop: 12,
  },
  buttonText: {
    color: '#fff',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  bottomActions: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  applyButton: {
    backgroundColor: '#3478f6',
    padding: 20,
    borderRadius: 180,
    alignItems: 'center',
    marginTop: 0,
  },
  linkText: {
    color: '#3478f6',
    fontSize: 18,
    textDecorationLine: 'underline',
    marginVertical: 4,
  },
  confirmBtn: {
    marginTop: 20,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  confirmText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
