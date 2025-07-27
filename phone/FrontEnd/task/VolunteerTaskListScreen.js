import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import { useNavigation, useIsFocused } from '@react-navigation/native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useActionSheet } from '@expo/react-native-action-sheet';
import { parseISO, format } from 'date-fns';
import { Ionicons } from '@expo/vector-icons';

import { BASE_URL } from '../config';
import { TYPOGRAPHY, COLORS, BUTTON_STYLE } from '../styles/theme';

export default function VolunteerTaskListScreen() {
  const [tasks, setTasks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const navigation = useNavigation();
  const isFocused = useIsFocused();
  const { showActionSheetWithOptions } = useActionSheet();

  const [filters, setFilters] = useState({
    keyword: '',
    weekday: '',
    time_block: '',
    work_area: '',
  });

  const weekdayLabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  const showPicker = (type) => {
    let options = [];
    let values = [];

    if (type === 'weekday') {
      options = ['Any', ...weekdayLabels];
      values = ['', ...weekdayLabels.map((_, i) => i.toString())];
    } else if (type === 'time_block') {
      options = ['Anytime', '08:00 - 11:00', '11:01 - 14:00', '14:01 - 17:00'];
      values = ['', 'morning', 'midday', 'afternoon'];
    } else if (type === 'work_area') {
      options = ['All',
        'Housekeeping', 'Meal preparation', 'Administrative Help', 'Companionship', 'Transport Assistance',
        'Laundry Assistance', 'Garden Maintenance', 'Reading Aloud', 'Pet Care', 'Childcare',
        'Prescription Pick-Up', 'Shopping Assistance', 'Cooking and Meal Planning',
        'Technology Assistance', 'Organisation and Decluttering', 'Crafts and Hobbies', 'Others'
      ];
      values = options.map(opt => (opt === 'All' ? '' : opt));
    }

    showActionSheetWithOptions(
      {
        options: [...options, 'Cancel'],
        cancelButtonIndex: options.length,
        title: `Select ${type.replace('_', ' ')}`,
      },
      (selectedIndex) => {
        if (selectedIndex !== undefined && selectedIndex !== options.length) {
          setFilters((prev) => ({
            ...prev,
            [type]: values[selectedIndex],
          }));
        }
      }
    );
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTasks(filters);
    setRefreshing(false);
  };

  useEffect(() => {
    if (isFocused) {
      fetchTasks(filters);
    }
  }, [isFocused]);

  const fetchTasks = async (filters = {}) => {
    try {
      const token = await AsyncStorage.getItem('userToken');

      const params = new URLSearchParams();
      if (filters.keyword) params.append('keyword', filters.keyword);
      if (filters.weekday !== '') params.append('weekday', filters.weekday);
      if (filters.time_block) params.append('time_block', filters.time_block);
      if (filters.work_area) params.append('work_area', filters.work_area);

      const res = await axios.get(`${BASE_URL}/mobile/task/list/?${params.toString()}`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (res.data.tasks) {
        setTasks(res.data.tasks);
      } else {
        console.warn('⚠️ Unexpected response:', res.data);
      }
    } catch (error) {
      console.error('❌ Failed to fetch tasks:', error.response?.data || error.message);
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.taskCard}
      onPress={() => navigation.navigate('TaskDetail', { taskId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.date}>
        {format(parseISO(item.start_time), "EEEE, d MMM yyyy · hh:mm a")} -{' '}
        {format(parseISO(item.end_time), "hh:mm a")}
      </Text>
      <Text style={styles.status}>Status: {item.status || 'Unknown'}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* 顶部搜索 + 刷新 */}
      <View style={styles.searchRefreshRow}>
        <TextInput
          style={styles.searchInput}
          value={filters.keyword}
          onChangeText={(text) => setFilters({ ...filters, keyword: text })}
          placeholder="Search title or description"
        />
        <TouchableOpacity onPress={() => fetchTasks(filters)} style={styles.iconButton}>
          <Ionicons name="search" size={22} color="#007bff" />
        </TouchableOpacity>
        <TouchableOpacity onPress={handleRefresh} style={styles.iconButton}>
          <Ionicons name="refresh" size={22} color="#007bff" />
        </TouchableOpacity>
      </View>

      {/* 三项筛选器 */}
      <View style={styles.filterRow}>
        <TouchableOpacity onPress={() => showPicker('weekday')} style={styles.filterButton}>
          <Text>Weekday {filters.weekday !== '' ? `: ${weekdayLabels[parseInt(filters.weekday)]}` : ''}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => showPicker('time_block')} style={styles.filterButton}>
          <Text>Time {filters.time_block ? `: ${filters.time_block}` : ''}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => showPicker('work_area')} style={styles.filterButton}>
          <Text>Area {filters.work_area ? `: ${filters.work_area}` : ''}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.actionRow}>
        <TouchableOpacity onPress={() => fetchTasks(filters)} style={[styles.applyButton]}>
          <Text style={TYPOGRAPHY.buttonText}>Apply Filters</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => {
            const cleared = { keyword: '', weekday: '', time_block: '', work_area: '' };
            setFilters(cleared);
            fetchTasks(cleared);
          }}
          style={styles.clearButton}
        >
          <Text style={TYPOGRAPHY.buttonText}>Clear</Text>
        </TouchableOpacity>
      </View>

      {/* 任务列表 */}
      <FlatList
        data={tasks}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={{ paddingBottom: 20 }}
        ListEmptyComponent={<Text>No tasks available now.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.background,
    flex: 1,
  },
  searchRefreshRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  searchInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 6,
    padding: 8,
    backgroundColor: '#fff',
  },
  filterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  filterButton: {
    backgroundColor: '#e0e0e0',
    padding: 8,
    borderRadius: 6,
    flex: 1,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  taskCard: {
    backgroundColor: '#fff',
    padding: 16,
    marginTop: 12,
    borderRadius: 8,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  date: {
    marginTop: 4,
    color: '#555',
  },
  status: {
    marginTop: 4,
    fontStyle: 'italic',
    color: COLORS.text,
  },
  searchRefreshRow: {
  flexDirection: 'row',
  alignItems: 'center',
  marginBottom: 10,
  },
  searchInput: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 10,
    backgroundColor: '#fff',
    marginRight: 8,
  },
  iconButton: {
    padding: 6,
    marginLeft: 4,
  },
  actionRow: {
  flexDirection: 'row',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginVertical: 12,
  },
  applyButton: {
    flex: 3,
    marginRight: 8,
    ...BUTTON_STYLE,
  },
  clearButton: {
    flex: 1,
    backgroundColor: '#ccc',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
});
