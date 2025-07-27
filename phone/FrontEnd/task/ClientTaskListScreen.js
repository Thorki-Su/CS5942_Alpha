import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet,ActivityIndicator } from 'react-native';
import { useNavigation,useIsFocused } from '@react-navigation/native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { parseISO, format } from 'date-fns';
import { Ionicons } from '@expo/vector-icons';

import { BASE_URL } from '../config';
import { TYPOGRAPHY, COLORS, BUTTON_STYLE } from '../styles/theme';

export default function ClientTaskListScreen() {
  const [selectedFilter, setSelectedFilter] = useState('open');
  const [tasks, setTasks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const navigation = useNavigation();
  const isFocused = useIsFocused();

  const fetchTasks = async () => {
      try {
        const token = await AsyncStorage.getItem('userToken');
        const res = await axios.get(`${BASE_URL}/mobile/task/my-tasks/`, {
          headers: { Authorization: `Token ${token}` },
        });

        if (res.data.tasks) {
          // console.log('✅ 获取任务成功:', res.data.tasks);
          setTasks(res.data.tasks);
        } else {
          console.warn('⚠️ 返回数据格式异常:', res.data);
        }
      } catch (error) {
        console.error('❌ 获取我的任务失败:', error.response?.data || error.message);
      }
    };

  useEffect(() => {
    fetchTasks();
  }, []);

  useEffect(() => {
    if (isFocused) {
      fetchTasks();
    }
  }, [isFocused]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTasks();
    setRefreshing(false);
  };

  // ⏳ 过滤任务
  const getFilteredTasks = () => {
  return tasks.filter((task) => {
    if (selectedFilter === 'ongoing') {
      return task.status === 'ongoing';
    }
    if (selectedFilter === 'open') {
      return task.status === 'open';
    }
    if (selectedFilter === 'finished') {
      return task.status === 'completed' || task.status === 'timeout';
    }
    return true;
  });
};
  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.taskCard}
      onPress={() => navigation.navigate('TaskDetail', { taskId: item.id })}
    >
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.date}>
        {format(parseISO(item.start_time), "EEEE, d MMMM yyyy · hh:mm a")} - {format(parseISO(item.end_time), "hh:mm a")}
      </Text>
      <Text style={styles.status}>Status: {item.status}</Text>
      <Text style={styles.createdAt}>
        Created: {format(parseISO(item.created_at), "yyyy-MM-dd HH:mm")}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={TYPOGRAPHY.title}>My Tasks</Text>
        <View style={styles.filterContainer}>
          <TouchableOpacity onPress={handleRefresh} style={styles.iconButton}>
            {refreshing ? (
              <ActivityIndicator size="small" color="#007bff" />
            ) : (
              <Ionicons name="refresh" size={22} color="#007bff" />
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterButton, selectedFilter === 'ongoing' && styles.activeFilter]}
            onPress={() => setSelectedFilter('ongoing')}
          >
            <Text style={styles.filterText}>Ongoing</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterButton, selectedFilter === 'open' && styles.activeFilter]}
            onPress={() => setSelectedFilter('open')}
          >
            <Text style={styles.filterText}>Open</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterButton, selectedFilter === 'finished' && styles.activeFilter]}
            onPress={() => setSelectedFilter('finished')}
          >
            <Text style={styles.filterText}>Finished</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterButton, selectedFilter === 'locked' && styles.activeFilter]}
            onPress={() => setSelectedFilter('locked')}
          >
            <Text style={styles.filterText}>All Tasks</Text>
          </TouchableOpacity>
        </View>
      </View>

      <FlatList
        data={getFilteredTasks()}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={{ paddingBottom: 20 }}
      />

      <TouchableOpacity
        style={[BUTTON_STYLE, { marginTop: 20 }]}
        onPress={() => navigation.navigate('CreateTask')}
      >
        <Text style={TYPOGRAPHY.buttonText}>+ Create New Task</Text>
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
  headerRow: {
    marginBottom: 8,
  },
    filterContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 6,
  },
  filterButton: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    marginLeft: 8,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  activeFilter: {
    backgroundColor: '#d1d1d1',  // 更深一些
    borderColor: '#999',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
    elevation: 1, // 低浮层 + 深色背景 = 内凹感
  },
  filterText: {
    fontSize: 13,
    color: '#000',
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
  refreshButton: {
    alignSelf: 'flex-end',
    padding: 6,
    marginBottom: 8,
    marginLeft: 0,
  },
  refreshText: {
    color: '#007bff',
    fontWeight: 'bold',
  },
  createdAt: {
    marginTop: 4,
    fontSize: 12,
    color: '#888',
  },
});
