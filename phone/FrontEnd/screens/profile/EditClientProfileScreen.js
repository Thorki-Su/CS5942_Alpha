import React, { useEffect, useState,useCallback } from 'react';
import { View, Text, TextInput, ScrollView, Button, Alert, Switch,TouchableOpacity, } from 'react-native';
import axios from 'axios';
import { useNavigation,useFocusEffect } from '@react-navigation/native';

import CollapsibleMultiSelect from '../../components/CollapsibleMultiSelect';
import SimpleMultiSelect from '../../components/SimpleMultiSelect';  
import { fetchUserProfile } from '../../components/fetchUserProfile';

import { BASE_URL } from '../../config';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CONDITIONS = [
  'M.E/CFS', 'Fibromyalgia', 'PTSD', 'Long Covid',
  'Lupus', 'Cutaneous Lupus', 'Others'
].map(item => ({ label: item, value: item }));

const SUPPORT_AREAS = [
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
  'Others',
].map(item => ({ label: item, value: item }));

const formatPreferredTimes = (times) => {
  if (!times || Object.keys(times).length === 0) return '(Not set)';
  return Object.entries(times)
    .map(([day, slots]) => `${day}: ${slots.join(', ')}`)
    .join(', ');
};

const EditClientProfileScreen = () => {
  const [profile, setProfile] = useState({});
  const [loading, setLoading] = useState(true);
  const navigation = useNavigation();

  useFocusEffect(
    useCallback(() => {
      const loadProfile = async () => {
        try {
          const data = await fetchUserProfile();  // 拉取 /api/mobile/profile/
          if (data) {
            const flatProfile = {
              ...data.user_profile,
              ...data.client_fields,  // 如果是 volunteer，可改为 ...data.volunteer_fields
            };
            // console.log('📥 拉取并设定 profile 数据:', flatProfile);
            setProfile(flatProfile);
          }
        } catch (err) {
          console.error('❌ 拉取 profile 出错:', err);
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
      const token = await AsyncStorage.getItem('userToken'); // 获取 token

      // console.log('🔑 Token:', token);  // ← token 检查点
      // console.log('🚀 Sending profile:', JSON.stringify(profile)); // ← 数据结构检查点

			const response = await axios.post(`${BASE_URL}/api/mobile/edit/client/`, profile, {
				headers: { Authorization: `Token ${token}` },
			});
      if (response.data.status === 'success') {
        Alert.alert('Success', 'Profile updated successfully.');
        // 🔄 保存成功后重新拉取用户资料并更新状态
      const updatedProfile = await fetchUserProfile();
      if (updatedProfile) {
        setProfile(updatedProfile);  // 假设你用 useState 保存了 profile
      }
      navigation.goBack();
      } else {
        Alert.alert('Error', 'Failed to update profile.');
      }
    } catch (error) {
      console.error('Update error:', error);
      console.log('❌ 后端返回:', error.response?.data); // ← 捕捉后端 400 错误内容

      Alert.alert('Error', 'Server error. Please try again.');
    }
  };

  if (loading) return <Text style={{ padding: 20 }}>Loading...</Text>;

  return (
    <ScrollView style={{ flex: 1 }}
			contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
			keyboardShouldPersistTaps="handled">
      {[
        ['first_name', 'First Name'],
        ['last_name', 'Last Name'],
        ['phone_number', 'Phone Number'],
        ['location', 'Location'],
        ['age', 'Age'],
        ['gender', 'Gender'],
        ['emergency_contact', 'Emergency Contact'],
        ['dietary_needs', 'Dietary Needs'],
        ['allergies', 'Allergies'],
        ['pets_type', 'Pets Type'],
        ['conditions', 'Conditions'],
        ['other_conditions', 'Other Conditions'],
        ['support_areas', 'Support Areas'],
        ['other_support', 'Other Support'],
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
            }}
          />
        </View>
      ))}

      <View style={{ marginBottom: 10 }}>
        <Text>Has Pets</Text>
        <Switch
          value={!!profile.has_pets}
          onValueChange={val => handleChange('has_pets', val)}
        />
      </View>

      {/* 可以添加上传按钮：pip/adp/lwc_certificate，等你准备好再做 */}
			<View style={{ marginBottom: 10 }}>
				<Text>PIP Certificate (Upload)</Text>
				<Button title="Upload File (Not implemented)" onPress={() => Alert.alert("⚠️ Upload not yet supported")} />
			</View>

			<CollapsibleMultiSelect
        label="Conditions You Live With"
        items={CONDITIONS}
        selectedItems={profile.conditions || []}
        onSelectionsChange={val => handleChange('conditions', val)}
        labelKey="label"
        valueKey="value"
      />

      <CollapsibleMultiSelect
        label="Support Areas"
        items={SUPPORT_AREAS}
        selectedItems={profile.support_areas || []}
        onSelectionsChange={val => handleChange('support_areas', val)}
        labelKey="label"
        valueKey="value"
      />
      {/* Preferred Times 显示与跳转 */}
      <View style={{ marginBottom: 10 }}>
        <Text style={{ fontWeight: 'bold' }}>Preferred Times</Text>
        <TouchableOpacity onPress={() => navigation.navigate('EditPreferredTimes')}>
          <Text style={{ color: '#007bff', marginTop: 4 }}>
            {formatPreferredTimes(profile.preferred_times)}
          </Text>
        </TouchableOpacity>
      </View>
      <Button title="Save" onPress={handleSubmit} />
    </ScrollView>
  );
};

export default EditClientProfileScreen;
