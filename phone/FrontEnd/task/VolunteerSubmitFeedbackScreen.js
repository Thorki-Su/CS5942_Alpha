import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet, TouchableOpacity, Alert,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Toast from 'react-native-toast-message';
import { BASE_URL } from '../config';
import { COLORS } from '../styles/theme';

export default function SubmitFeedbackScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { taskId, toUserId } = route.params;

  const [isSatisfied, setIsSatisfied] = useState(true);
  const [comment, setComment] = useState('');

  const submitFeedback = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      await axios.post(`${BASE_URL}/mobile/task/volunteer/feedback/${taskId}/`, {
        // to_user_id: toUserId,
        is_satisfied: isSatisfied,
        comment: comment,
      }, {
        headers: { Authorization: `Token ${token}` },
      });

      Toast.show({
        type: 'success',
        text1: 'Feedback submitted successfully',
      });
      navigation.goBack();
    } catch (err) {
      console.error('Submit feedback failed:', err);
      Toast.show({
        type: 'error',
        text1: 'Failed to submit feedback',
      });
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Are you satisfied with the client?</Text>
      <View style={styles.row}>
        <TouchableOpacity
          style={[styles.option, isSatisfied && styles.selectedOption]}
          onPress={() => setIsSatisfied(true)}
        >
          <Text style={isSatisfied ? styles.selectedText : styles.optionText}>Satisfied</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.option, !isSatisfied && styles.selectedOption]}
          onPress={() => setIsSatisfied(false)}
        >
          <Text style={!isSatisfied ? styles.selectedText : styles.optionText}>Not Satisfied</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.label}>Comment:</Text>
      <TextInput
        style={styles.input}
        placeholder="Write your feedback..."
        multiline
        value={comment}
        onChangeText={setComment}
      />

      <TouchableOpacity style={styles.submitBtn} onPress={submitFeedback}>
        <Text style={styles.submitText}>Submit Feedback</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
    flex: 1,
  },
  label: {
    fontSize: 16,
    marginTop: 12,
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 6,
    height: 120,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 10,
  },
  option: {
    padding: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  selectedOption: {
    backgroundColor: COLORS.primary,
  },
  optionText: {
    color: COLORS.primary,
  },
  selectedText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  submitBtn: {
    marginTop: 20,
		backgroundColor: COLORS.primary,
		paddingVertical: 12,
		paddingHorizontal: 20,
		borderRadius: 8,
		alignItems: 'center',
  },
  submitText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
