import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView, Alert, StyleSheet,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { BASE_URL } from '../config';
import { COLORS, TYPOGRAPHY } from '../styles/theme';

export default function VolunteerSubmitRecordScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { taskId } = route.params;

  const [records, setRecords] = useState(['']);
  const [taskTitle, setTaskTitle] = useState('');

  useEffect(() => {
    const fetchTaskTitle = async () => {
      const token = await AsyncStorage.getItem('userToken');
      try {
        const res = await axios.get(`${BASE_URL}/mobile/task/${taskId}/`, {
          headers: { Authorization: `Token ${token}` },
        });
        setTaskTitle(res.data.title || 'Untitled Task');
      } catch (err) {
        console.error('❌ 获取任务标题失败:', err.response?.data || err.message);
      }
    };

    fetchTaskTitle();
  }, [taskId]);

  const updateRecord = (text, index) => {
    const updated = [...records];
    updated[index] = text;
    setRecords(updated);
  };

  const addRecord = () => setRecords([...records, '']);
  const removeRecord = (index) => {
    const updated = records.filter((_, i) => i !== index);
    setRecords(updated.length > 0 ? updated : ['']);
  };

  const handleSubmit = async () => {
    const cleanedRecords = records.map(r => r.trim()).filter(r => r);
    if (cleanedRecords.length === 0) {
      Alert.alert('Error', 'Please enter at least one record item.');
      return;
    }

    try {
      const token = await AsyncStorage.getItem('userToken');
      await axios.post(`${BASE_URL}/mobile/task/${taskId}/submit-record/`, {
        records: cleanedRecords,
      }, {
        headers: { Authorization: `Token ${token}` },
      });

      Alert.alert('Success', 'Task record submitted.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      console.error('❌ 提交记录失败:', err.response?.data || err.message);
      Alert.alert('Error', 'Failed to submit task record.');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Task Record</Text>
      <Text style={styles.subtitle}>Task: {taskTitle}</Text>

      {records.map((record, index) => (
        <View key={index} style={styles.recordItem}>
          <TextInput
            style={styles.input}
            value={record}
            onChangeText={(text) => updateRecord(text, index)}
            placeholder={`Record ${index + 1}`}
          />
          <TouchableOpacity onPress={() => removeRecord(index)}>
            <Text style={styles.removeBtn}>✕</Text>
          </TouchableOpacity>
        </View>
      ))}

      <TouchableOpacity onPress={addRecord} style={styles.addButton}>
        <Text style={styles.addButtonText}>+ Add Another Record</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={handleSubmit} style={styles.submitButton}>
        <Text style={styles.submitButtonText}>Submit Record</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
    flex: 1,
  },
  title: {
    ...TYPOGRAPHY.title,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 24,
  },
  recordItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  input: {
    flex: 1,
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    backgroundColor: '#fff',
  },
  removeBtn: {
    color: 'red',
    fontSize: 20,
    marginLeft: 8,
    paddingHorizontal: 6,
  },
  addButton: {
    marginTop: 12,
    backgroundColor: '#e0e0e0',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#333',
    fontWeight: 'bold',
  },
  submitButton: {
    marginTop: 24,
    backgroundColor: COLORS.primary,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
