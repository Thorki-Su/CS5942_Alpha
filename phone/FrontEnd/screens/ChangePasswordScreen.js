import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableWithoutFeedback,
  Keyboard,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { BASE_URL } from '../config'; // 确保你设置了 BASE_URL

export default function ChangePasswordScreen({ navigation }) {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword) {
      Alert.alert('请填写完整');
      return;
    }

    try {
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        Alert.alert('未登录', '请重新登录');
        return;
      }

      const response = await axios.patch(
        `${BASE_URL}/api/mobile/change_password/`,
        {
          old_password: oldPassword,
          new_password: newPassword,
        },
        {
          headers: {
            Authorization: `Token ${token}`,
          },
        }
      );

      if (response.status === 200 || response.data.status === 'success') {
        Alert.alert('密码修改成功');
        navigation.goBack();
      } else {
        Alert.alert('密码修改失败', '请重试');
      }
    } catch (error) {
      console.error('❌ 修改密码失败:', error.response?.data || error.message);
      const errMsg = error.response?.data?.error || '服务器错误';
      Alert.alert('密码修改失败', errMsg);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', padding: 20 }}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={{ fontSize: 22, marginBottom: 12 }}>修改密码</Text>

          <TextInput
            placeholder="原密码"
            value={oldPassword}
            secureTextEntry
            onChangeText={setOldPassword}
            style={{ borderWidth: 1, padding: 8, marginBottom: 12 }}
          />

          <TextInput
            placeholder="新密码"
            value={newPassword}
            secureTextEntry
            onChangeText={setNewPassword}
            style={{ borderWidth: 1, padding: 8, marginBottom: 12 }}
          />

          <Button title="确认修改" onPress={handleChangePassword} />
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}
