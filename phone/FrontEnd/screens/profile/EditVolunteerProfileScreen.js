// screens/profile/EditVolunteerProfileScreen.js

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  Button,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import axios from 'axios';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { BASE_URL } from '../../config';
import { fetchUserProfile } from '../../components/fetchUserProfile';
import SimpleMultiSelect from '../../components/SimpleMultiSelect';
import CollapsibleMultiSelect from '../../components/CollapsibleMultiSelect';

const TASK_OPTIONS = [
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
  'Language Support',
  'Befriending',
  'Emotional Support',
  'Others',
];
const PVG_LEVEL_OPTIONS = [
  { label: 'Verified', value: 'verified' },
  { label: 'Processing', value: 'processing' },
  { label: 'Pending', value: 'pending' },
  { label: 'I do not have a PVG yet', value: 'do_not_have' },
];

const EditVolunteerProfileScreen = () => {
  const [profile, setProfile] = useState({});
  const [loading, setLoading] = useState(true);
  const navigation = useNavigation();

  useFocusEffect(
    useCallback(() => {
      const loadProfile = async () => {
        try {
          const data = await fetchUserProfile();
          if (data) {
            const flatProfile = {
              ...data.user_profile,
              ...data.volunteer_fields,
            };
            setProfile(flatProfile);
          }
        } catch (err) {
          console.error('❌ 拉取 volunteer profile 出错:', err);
        } finally {
          setLoading(false);
        }
      };
      loadProfile();
    }, [])
  );

  const handleChange = (key, value) => {
    setProfile(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      console.log('🔑 Token:', token);  // ← token 检查点
      // console.log('🚀 Sending profile:', JSON.stringify(profile)); // ← 数据结构检查点
			console.log('📤 即将提交的 preferred_tasks:', profile.preferred_tasks);
			console.log('📤 类型：', typeof profile.preferred_tasks);
			console.log('📤 是否数组：', Array.isArray(profile.preferred_tasks));
      const response = await axios.post(`${BASE_URL}/api/mobile/edit/volunteer/`, profile, {
        headers: { Authorization: `Token ${token}` },
      });
      if (response.data.status === 'success') {
        Alert.alert('Success', 'Profile updated successfully.');
        const updatedProfile = await fetchUserProfile();
        if (updatedProfile) {
          setProfile(updatedProfile);
        }
        navigation.goBack();
      } else {
				console.log('📩 返回状态码:', response.status);
				console.log('📩 返回数据内容:', response.data);
        Alert.alert('Error', 'Failed to update profile.');
      }
    } catch (error) {
      console.error('❌ Axios 捕获错误:', error);
			console.log('❌ 返回状态码:', error.response?.status);
      console.log('❌ 后端返回:', error.response?.data);
      Alert.alert('Error', 'Server error. Please try again.');
    }
  };

  if (loading) return <Text style={{ padding: 20 }}>Loading...</Text>;

  return (
    <ScrollView
      style={{ flex: 1 }}
      contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
      keyboardShouldPersistTaps="handled"
    >
      {[
        ['first_name', 'First Name'],
        ['last_name', 'Last Name'],
        ['phone_number', 'Phone Number'],
        ['location', 'Location'],
        ['age', 'Age'],
        ['gender', 'Gender'],
        ['emergency_contact', 'Emergency Contact'],
        ['skills', 'Skills'],
        ['interests', 'Interests'],
        ['motivation', 'Motivation'],
      ].map(([key, label]) => (
        <View key={key} style={{ marginBottom: 10 }}>
          <Text>{label}</Text>
          <TextInput
            value={profile[key] || ''}
            onChangeText={text => handleChange(key, text)}
            style={{
              borderWidth: 1,
              borderColor: '#ccc',
              borderRadius: 5,
              padding: 8,
              height: key === 'motivation' ? 80 : undefined,
              textAlignVertical: key === 'motivation' ? 'top' : 'center',
            }}
            multiline={key === 'motivation'}
          />
        </View>
      ))}

      <CollapsibleMultiSelect
        label="Preferred Tasks"
        options={TASK_OPTIONS}
        selected={profile.preferred_tasks || []}
        onChange={val => handleChange('preferred_tasks', val)}
      />

      <View style={{ marginBottom: 10 }}>
        <Text>PVG Level</Text>
        <Picker
            selectedValue={profile.pvg_level || ''}
            onValueChange={(val) => handleChange('pvg_level', val)}
            style={{ borderWidth: 1, borderColor: '#ccc', borderRadius: 5 }}
        >
            {PVG_LEVEL_OPTIONS.map((option) => (
            <Picker.Item key={option.value} label={option.label} value={option.value} />
            ))}
        </Picker>
			</View>

      <View style={{ marginBottom: 10 }}>
        <Text>PVG File (Upload)</Text>
        <Button title="Upload File (Not implemented)" onPress={() => Alert.alert("⚠️ Upload not yet supported")} />
      </View>

      <View style={{ marginTop: 20 }}>
        <Button title="Save" onPress={handleSubmit} />
      </View>
    </ScrollView>
  );
};

export default EditVolunteerProfileScreen;
