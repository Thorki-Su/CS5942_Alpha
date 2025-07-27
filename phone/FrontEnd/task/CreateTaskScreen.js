import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import CollapsibleMultiSelect from '../components/CollapsibleMultiSelect';
import { BASE_URL } from '../config';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const workAreaOptions = [
  'Housekeeping',
  'Meal preparation',
  'Administrative Help',
  'Companionship',
  'Transport Assistance',
  'Laundry Assistance',
  'Garden Maintenance',
  'Reading Aloud',
  'Pet Care',
  'Childcare',
  'Prescription Pick-Up',
  'Shopping Assistance',
  'Cooking and Meal Planning',
  'Technology Assistance',
  'Organisation and Decluttering',
  'Crafts and Hobbies',
  // 'Language Support',
  // 'Befriending',
  // 'Emotional Support',
  'Others',
];

export default function CreateTaskScreen({ navigation }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startTime, setStartTime] = useState(new Date());
  const [tempStartTime, setTempStartTime] = useState(new Date());
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [endTime, setEndTime] = useState(new Date());
  const [tempEndTime, setTempEndTime] = useState(new Date());
  const [showEndPicker, setShowEndPicker] = useState(false);
  const [volNumber, setVolNumber] = useState('');
  const [workAreas, setWorkAreas] = useState([]);
  const [workAreaOptions, setWorkAreaOptions] = useState([]);

  useEffect(() => {
    fetchWorkAreas();
  }, []);

  const fetchWorkAreas = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const response = await axios.get(`${BASE_URL}/mobile/task/work-areas/`, {
			headers: { Authorization: `Token ${token}` }
			});
			// console.log("✅ 成功拉取 work_area:", response.data);
			setWorkAreaOptions(response.data);
    } catch (e) {
      console.error('❌ 拉取 work_area 失败:', e);
    }
  };

  const handleCreateTask = async () => {
    if (!title || !description || !startTime || !endTime || !volNumber) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }

    try {
      const token = await AsyncStorage.getItem('userToken');
      const payload = {
        title,
        description,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        vol_number: parseInt(volNumber),
        work_area: workAreas,
      };

      const res = await axios.post(`${BASE_URL}/mobile/task/create/`, payload, {
        headers: { Authorization: `Token ${token}` },
      });

      if (res.data?.success) {
        Alert.alert('Success', 'Task created successfully!');
        navigation.goBack();
      }
    } catch (e) {
      console.error('❌ 创建任务失败:', e);
      Alert.alert('Error', 'Task creation failed.');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.label}>1. Task Title:</Text>
      <TextInput value={title} onChangeText={setTitle} style={styles.input} />

      <Text style={styles.label}>2. Description:</Text>
      <TextInput
        value={description}
        onChangeText={setDescription}
        style={[styles.input, { height: 100 }]}
        multiline
      />

      <Text style={styles.label}>3. Start Time:</Text>
      <TouchableOpacity onPress={() => setShowStartPicker(true)}>
        <Text style={styles.input}>{startTime.toLocaleString()}</Text>
      </TouchableOpacity>
      {/* // 修改 onChange 行为 */}
        {showStartPicker && (
          <DateTimePicker
            value={tempStartTime}
            mode="datetime"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(e, selectedDate) => {
              if (Platform.OS === 'android') {
                // Android 上点击确定就设定
                setShowStartPicker(false);
                if (selectedDate) {
                  setStartTime(selectedDate);
                  setTempStartTime(selectedDate);
                }
              } else {
                // iOS 上不自动关闭
                if (selectedDate) {
                  setTempStartTime(selectedDate);
                }
              }
            }}
          />
        )}
        {/* // iOS 专属确认按钮 */}
        {Platform.OS === 'ios' && showStartPicker && (
          <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginTop: 10 }}>
            <TouchableOpacity
              onPress={() => {
                setStartTime(tempStartTime);
                setShowStartPicker(false);
              }}
            >
              <Text style={{ color: 'blue', fontSize: 16, marginRight: 20 }}>Confirm</Text>
            </TouchableOpacity>
          </View>
        )}

      <Text style={styles.label}>4. End Time:</Text>
      <TouchableOpacity onPress={() => setShowEndPicker(true)}>
        <Text style={styles.input}>{endTime.toLocaleString()}</Text>
      </TouchableOpacity>
         {/* 修改 onChange 行为 */}
        {showEndPicker && (
          <DateTimePicker
            value={tempEndTime}
            mode="datetime"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(e, selectedDate) => {
              if (Platform.OS === 'android') {
                // Android 上点击确定就设定
                setShowEndPicker(false);
                if (selectedDate) {
                  setEndTime(selectedDate);
                  setTempEndTime(selectedDate);
                }
              } else {
                // iOS 上不自动关闭
                if (selectedDate) {
                  setTempEndTime(selectedDate);
                }
              }
            }}
          />
        )}
         {/* iOS 专属确认按钮 */}
        {Platform.OS === 'ios' && showEndPicker && (
          <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginTop: 10 }}>
            <TouchableOpacity
              onPress={() => {
                setEndTime(tempEndTime);
                setShowEndPicker(false);
              }}
            >
              <Text style={{ color: 'blue', fontSize: 16, marginRight: 20 }}>Confirm</Text>
            </TouchableOpacity>
          </View>
        )}

      <Text style={styles.label}>5. Volunteer Number:</Text>
      <TextInput
        value={volNumber}
        onChangeText={setVolNumber}
        keyboardType="numeric"
        style={styles.input}
      />

      <Text style={styles.label}></Text>
      {Array.isArray(workAreaOptions) && (
				<CollapsibleMultiSelect
					label="6. Support Area:"
					items={workAreaOptions}               // eg: [{label: 'xxx', value: 1}]
					selectedItems={workAreas}            // eg: [1, 4, 9]
					onSelectionsChange={setWorkAreas}
					labelKey="label"
					valueKey="value"
				/>
			)}

      <View style={{ marginTop: 30 }}>
        <Button title="Post Task" onPress={handleCreateTask} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
  },
  label: {
    fontWeight: 'bold',
    marginTop: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginTop: 5,
  },
});
