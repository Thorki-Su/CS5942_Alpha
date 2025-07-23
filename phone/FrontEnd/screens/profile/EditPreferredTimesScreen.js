// screens/profile/EditPreferredTimesScreen.js

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BASE_URL } from '../../config';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIME_SLOTS = [
  '08:00-11:00',
  '11:00-14:00',
  '14:00-17:00',
  '17:00-20:00',
  '20:00-23:00',
];

const EditPreferredTimesScreen = () => {
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  const loadInitial = async () => {
    try {
			const token = await AsyncStorage.getItem('token');
			const res = await fetch(`${BASE_URL}/api/mobile/profile/`, {
				headers: { Authorization: `Token ${token}` },
			});
			const data = await res.json();
			setSelected(data.client_fields.preferred_times || {});  // 正常设置 selected
      } catch (err) {
        console.warn('加载初始 preferred_times 失败:', err);
      } finally {
        setLoading(false);
      }
    };
    loadInitial();
  }, []);

  const toggleSelection = (day, slot) => {
    setSelected((prev) => {
      const current = prev[day] || [];
      const newSlots = current.includes(slot)
        ? current.filter((t) => t !== slot)
        : [...current, slot];
      return { ...prev, [day]: newSlots };
    });
  };

  const isSelected = (day, slot) => {
    return selected[day]?.includes(slot);
  };

  const handleSave = async () => {
		const cleanSelected = Object.fromEntries(
			Object.entries(selected).filter(([day, slots]) => Array.isArray(slots) && slots.length > 0)
		);
    try {
      const token = await AsyncStorage.getItem('token');
      const res = await fetch(`${BASE_URL}/api/mobile/save_preferred_times/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify(cleanSelected),
      });

      if (res.ok) {
        Alert.alert('✅ 保存成功');
      } else {
        Alert.alert('❌ 保存失败');
      }
    } catch (err) {
      Alert.alert('❌ 网络错误:', err.message);
    }
  };

  if (loading) return <ActivityIndicator size="large" style={{ marginTop: 100 }} />;

  return (
    <ScrollView horizontal>
      <View>
        <View style={styles.headerRow}>
          <View style={styles.cell} />
          {DAYS.map((day) => (
            <View key={day} style={styles.cell}>
              <Text style={styles.headerText}>{day}</Text>
            </View>
          ))}
        </View>

        {TIME_SLOTS.map((slot) => (
          <View key={slot} style={styles.row}>
            <View style={styles.cell}>
              <Text style={styles.slotText}>{slot}</Text>
            </View>
            {DAYS.map((day) => (
              <TouchableOpacity
                key={`${day}-${slot}`}
                style={[
                  styles.cell,
                  isSelected(day, slot) && styles.selectedCell,
                ]}
                onPress={() => toggleSelection(day, slot)}
              >
                {isSelected(day, slot) && <Text style={styles.checkmark}>✓</Text>}
              </TouchableOpacity>
            ))}
          </View>
        ))}

        <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
          <Text style={styles.saveText}>Save Preferred Times</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

export default EditPreferredTimesScreen;

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row' },
  row: { flexDirection: 'row' },
  cell: {
    width: 100,
    height: 50,
    borderWidth: 1,
    borderColor: '#ccc',
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectedCell: {
    backgroundColor: '#d0f0c0',
    borderColor: '#28a745',
  },
  headerText: {
    fontWeight: 'bold',
    textAlign: 'center',
  },
  slotText: {
    fontSize: 12,
    textAlign: 'center',
  },
  checkmark: {
    color: '#28a745',
    fontSize: 16,
  },
  saveButton: {
    marginTop: 20,
    padding: 12,
    backgroundColor: '#28a745',
    borderRadius: 6,
    alignItems: 'center',
  },
  saveText: {
    color: 'white',
    fontWeight: 'bold',
  },
});
