import React, { useState, useEffect } from 'react';
import { View, 
Text, 
StyleSheet, 
TouchableOpacity, 
Alert, 
Modal, 
Image, 
TouchableWithoutFeedback, 
Linking} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Toast from 'react-native-toast-message';
import { COLORS, TYPOGRAPHY } from '../styles/theme';
import { BASE_URL } from '../config';

export default function VolunteerApplicationDetailScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { application } = route.params;

  const [feedback, setFeedback] = useState(null);
  const [receivedFeedback, setReceivedFeedback] = useState(null);
  
  const [clientInfo, setClientInfo] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const fullName = clientInfo?.user
    ? `${clientInfo.user.first_name || ''} ${clientInfo.user.last_name || ''}`.trim()
    : '';


  const fetchTaskDetail = async () => {
    try {
      // console.log("🧩 application 内容", application);
      const token = await AsyncStorage.getItem('userToken');
      const res = await axios.get(`${BASE_URL}/mobile/task/${application.task_id}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setFeedback(res.data.feedback);
      setReceivedFeedback(res.data.received_feedback);
    } catch (err) {
      console.error('Fetch task detail failed:', err);
    }
  };

  const fetchClientInfo = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const clientId = application.client_id;
      const res = await axios.get(`${BASE_URL}/api/mobile/public_profile/${clientId}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      setClientInfo(res.data);
      setModalVisible(true);
    } catch (error) {
      console.error("❌ 获取 client 公开信息失败:", error);
    }
  };

  useEffect(() => {
    fetchTaskDetail();
    const unsubscribe = navigation.addListener('focus', fetchTaskDetail);
    return unsubscribe;
  }, [navigation]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const handleCancel = async () => {
    Alert.alert(
      'Confirm Cancel',
      'Are you sure you want to cancel your application?',
      [
        { text: 'No' },
        {
          text: 'Yes',
          onPress: async () => {
            try {
              const token = await AsyncStorage.getItem('userToken');
              await axios.post(`${BASE_URL}/mobile/task/volunteer/applications/${application.id}/cancel/`, {}, {
                headers: { Authorization: `Token ${token}` },
              });
              Toast.show({ type: 'success', text1: 'Cancelled successfully' });
              navigation.navigate('VolunteerMyApplicationsScreen', { refresh: true });
            } catch (err) {
              console.error('Cancel error:', err);
              Toast.show({ type: 'error', text1: 'Failed to cancel' });
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Text style={TYPOGRAPHY.title}>{application.title}</Text>

      <TouchableOpacity onPress={fetchClientInfo}>
        <Text style={{ color: COLORS.primary, marginTop: 4, marginBottom: 8 }}>
          Created by {application.client?.username || 'Client'}
        </Text>
      </TouchableOpacity>

      <Text style={styles.label}>Time:</Text>
      <Text style={styles.value}>
        {formatDate(application.start_time)} → {formatDate(application.end_time)}
      </Text>
      <Text style={styles.label}>Application Status:</Text>
      <Text style={styles.value}>{application.status}</Text>
      <Text style={styles.label}>Task Status:</Text>
      <Text style={styles.value}>{application.task_status}</Text>
      <Text style={styles.label}>Applied At:</Text>
      <Text style={styles.value}>{formatDate(application.applied_at)}</Text>

      {application.status === 'pending' && (
        <TouchableOpacity style={styles.cancelButton} onPress={handleCancel}>
          <Text style={styles.cancelText}>Cancel Application</Text>
        </TouchableOpacity>
      )}

      {feedback ? (
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Your Feedback</Text>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Satisfied:</Text>
            <Text
              style={[
                styles.feedbackValue,
                feedback.is_satisfied ? styles.satisfied : styles.unsatisfied,
              ]}
            >
              {feedback.is_satisfied ? 'Yes' : 'No'}
            </Text>
          </View>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Comment:</Text>
          </View>
          <Text style={styles.feedbackComment}>{feedback.comment || 'No comment'}</Text>
        </View>
      ) : (
        application.status === 'accepted' &&
        application.task_status === 'completed' &&
        !feedback && (
          <TouchableOpacity
            style={styles.feedbackBtn}
            onPress={() => navigation.navigate('VolunteerSubmitFeedback', {
              taskId: application.task_id,
              toUserId: application.client_id,
            })}
          >
            <Text style={styles.feedbackText}>Submit Feedback</Text>
          </TouchableOpacity>
        )
      )}

      {receivedFeedback && (
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Client's Feedback</Text>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>From:</Text>
            <Text style={styles.feedbackValue}>{receivedFeedback.from_user_name}</Text>
          </View>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Satisfied:</Text>
            <Text
              style={[
                styles.feedbackValue,
                receivedFeedback.is_satisfied ? styles.satisfied : styles.unsatisfied,
              ]}
            >
              {receivedFeedback.is_satisfied ? 'Yes' : 'No'}
            </Text>
          </View>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Comment:</Text>
          </View>
          <Text style={styles.feedbackComment}>
            {receivedFeedback.comment || 'No comment'}
          </Text>
        </View>
      )}

      {application.status === 'accepted' && application.task_status === 'ongoing' && (
        <TouchableOpacity
          style={styles.recordButton}
          onPress={() => navigation.navigate('VolunteerSubmitRecord', { taskId: application.task_id })}
        >
          <Text style={styles.recordButtonText}>Submit Task Record</Text>
        </TouchableOpacity>
      )}

      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <View style={{
            flex: 1, justifyContent: 'center', alignItems: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.5)'
          }}>
            <View style={{
              width: '80%', backgroundColor: 'white', borderRadius: 12,
              padding: 20, alignItems: 'center'
            }}>
              {clientInfo ? (
                <>
                  {clientInfo.user_profile.profile_photo && (
                    <Image
                      source={{ uri: clientInfo.user_profile.profile_photo }}
                      style={{ width: 80, height: 80, borderRadius: 40, marginBottom: 12 }}
                    />
                  )}
                  <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
                    {fullName || 'Unnamed User'}
                  </Text>
                  <Text style={{ marginBottom: 4 }}>
                    Gender: {clientInfo.user_profile.gender || 'N/A'}
                  </Text>
                  <Text style={{ marginBottom: 12 }}>
                    Age: {clientInfo.user_profile.age || 'N/A'}
                  </Text>

                  <TouchableOpacity
                    style={[styles.callButton, { marginBottom: 12 }]}
                    onPress={() => {
                        const phone = clientInfo?.user_profile?.phone_number;
                        if (phone) {
                          Linking.openURL(`tel:${phone}`);
                        } else {
                          Alert.alert("Phone number not available");
                        }
                      }}
                    >
                    <Text style={styles.callButtonText}>普通通话</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.feedbackBtn}
                    onPress={() => {
                      setModalVisible(false);
                      navigation.navigate('VideoCallTest', {
                        userId: application.volunteer_id,
                        targetId: application.client.id,
                      });
                    }}
                  >
                    <Text style={styles.feedbackText}>发起视频通话</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <Text>Loading...</Text>
              )}
            </View>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
    flex: 1,
  },
  createdBy: {
    fontSize:16,
    marginTop: 4,
    fontStyle: 'italic',
    color: COLORS.primary || '#666',
  },
  label: {
    marginTop: 12,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  value: {
    color: COLORS.text,
    marginBottom: 4,
  },
  cancelButton: {
    marginTop: 30,
    padding: 12,
    backgroundColor: COLORS.danger || 'red',
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  feedbackBtn: {
    marginTop: 20,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  feedbackText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  feedbackCard: {
    backgroundColor: '#fff',
    paddingVertical: 20,
    paddingHorizontal: 24,
    borderRadius: 16,
    marginTop: 28,
    marginBottom: 24,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
  },
  feedbackTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: COLORS.primary,
  },
  feedbackRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  feedbackLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginRight: 6,
    color: COLORS.text,
    width: 80,
  },
  feedbackValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  satisfied: {
    color: 'green',
  },
  unsatisfied: {
    color: 'red',
  },
  feedbackComment: {
    fontSize: 16,
    color: COLORS.text,
    marginTop: 4,
    lineHeight: 22,
  },
  recordButton: {
    backgroundColor: '#007bff',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
  },
  recordButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: '#fff',
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 12,
  },
  modalName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  modalText: {
    fontSize: 14,
    marginBottom: 4,
  },
  modalBtnGroup: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 12,
  },
  callBtn: {
    backgroundColor: '#28a745',
    padding: 10,
    borderRadius: 8,
  },
  videoBtn: {
    backgroundColor: '#17a2b8',
    padding: 10,
    borderRadius: 8,
  },
  callBtnText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  callButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
    marginTop: 12,
    alignItems: 'center',
  },
  callButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
