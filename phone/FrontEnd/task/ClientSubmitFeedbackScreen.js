import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TextInput,
  TouchableOpacity, Alert, ActivityIndicator
} from 'react-native';
import axios from 'axios';
import { useRoute, useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BASE_URL } from '../config';
import { COLORS } from '../styles/theme';

export default function ClientSubmitFeedbackScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { taskId, volunteerId } = route.params;

  const [loading, setLoading] = useState(true);
  const [volunteerName, setVolunteerName] = useState('');
  const [taskTitle, setTaskTitle] = useState('');
  const [isSatisfied, setIsSatisfied] = useState(null);
  const [comment, setComment] = useState('');
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [volunteerFeedback, setVolunteerFeedback] = useState(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      const token = await AsyncStorage.getItem('userToken');
      try {
        const res = await axios.get(`${BASE_URL}/mobile/task/${taskId}/client/feedback/${volunteerId}/`, {
          headers: { Authorization: `Token ${token}` },
        });
        setVolunteerName(res.data.volunteer_name);
        setTaskTitle(res.data.task_title);
        if (res.data.feedback) {
          setHasSubmitted(true);
          setIsSatisfied(res.data.feedback.is_satisfied);
          setComment(res.data.feedback.comment);
        }
        if (res.data.volunteer_feedback) {
          setVolunteerFeedback(res.data.volunteer_feedback);
        }
      } catch (err) {
        console.error('❌ 加载反馈信息失败:', err.response?.data || err.message);
        Alert.alert('Error', 'Failed to load feedback info');
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const submitFeedback = async () => {
    if (isSatisfied === null) {
      Alert.alert('Please select whether you are satisfied');
      return;
    }

    const token = await AsyncStorage.getItem('userToken');
    try {
      await axios.post(`${BASE_URL}/mobile/task/${taskId}/client/feedback/${volunteerId}/`, {
        is_satisfied: isSatisfied,
        comment: comment.trim(),
      }, {
        headers: { Authorization: `Token ${token}` },
      });
      Alert.alert('Success', 'Feedback submitted successfully.');
      navigation.goBack();
    } catch (err) {
      console.error('❌ 提交反馈失败:', err.response?.data || err.message);
      Alert.alert('Error', 'Failed to submit feedback.');
    }
  };

  if (loading) return <ActivityIndicator style={{ marginTop: 100 }} />;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Feedback for {volunteerName}</Text>
      <Text style={styles.subtitle}>Task: {taskTitle}</Text>

      {hasSubmitted ? (
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Your Feedback</Text>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Satisfied:</Text>
            <Text
              style={[styles.feedbackValue, isSatisfied ? styles.satisfied : styles.unsatisfied]}
            >
              {isSatisfied ? 'Yes' : 'No'}
            </Text>
          </View>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Comment:</Text>
          </View>
          <Text style={styles.feedbackComment}>{comment || 'No comment'}</Text>
        </View>
      ) : (
        <>
          <Text style={styles.label}>Are you satisfied?</Text>
          <View style={styles.row}>
            <TouchableOpacity
              style={[styles.option, isSatisfied === true && styles.selectedOption]}
              onPress={() => setIsSatisfied(true)}
            >
              <Text style={[styles.optionText, isSatisfied === true && styles.selectedText]}>✅ Yes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.option, isSatisfied === false && styles.selectedOption]}
              onPress={() => setIsSatisfied(false)}
            >
              <Text style={[styles.optionText, isSatisfied === false && styles.selectedText]}>❌ No</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.label}>Comment:</Text>
          <TextInput
            style={styles.input}
            placeholder="Write your feedback..."
            value={comment}
            onChangeText={setComment}
            multiline
          />

          <TouchableOpacity style={styles.submitBtn} onPress={submitFeedback}>
            <Text style={styles.submitText}>Submit Feedback</Text>
          </TouchableOpacity>
        </>
      )}

      {volunteerFeedback && (
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Volunteer Feedback</Text>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Satisfied:</Text>
            <Text
              style={[styles.feedbackValue, volunteerFeedback.is_satisfied ? styles.satisfied : styles.unsatisfied]}
            >
              {volunteerFeedback.is_satisfied ? 'Yes' : 'No'}
            </Text>
          </View>

          <View style={styles.feedbackRow}>
            <Text style={styles.feedbackLabel}>Comment:</Text>
          </View>
          <Text style={styles.feedbackComment}>{volunteerFeedback.comment || 'No comment'}</Text>
        </View>
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
  title: { fontSize: 20, fontWeight: 'bold' },
  subtitle: { fontSize: 16, marginBottom: 20 },
  label: { fontWeight: '600', marginTop: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-around', marginVertical: 10 },
  option: {
    padding: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  selectedOption: { backgroundColor: COLORS.primary },
  optionText: { color: COLORS.primary },
  selectedText: { color: '#fff', fontWeight: 'bold' },
  input: {
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 6,
    height: 120,
    textAlignVertical: 'top',
  },
  submitBtn: {
    marginTop: 20,
    backgroundColor: COLORS.primary,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
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
  satisfied: { color: 'green' },
  unsatisfied: { color: 'red' },
  feedbackComment: {
    fontSize: 16,
    color: COLORS.text,
    marginTop: 4,
    lineHeight: 22,
  },
});
