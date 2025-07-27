// screens/StartupScreen.js
import React, { useEffect } from 'react';
import { View, ActivityIndicator, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BASE_URL } from '../config';

export default function StartupScreen({ navigation }) {
  useEffect(() => {
    console.log("🧭 StartupScreen 已挂载");
    const checkLogin = async () => {
      try {
        const email = await AsyncStorage.getItem('loggedInEmail');
        const token = await AsyncStorage.getItem('userToken');
        console.log('🚀 正在检查登录状态...');
        console.log('📧 Email:', email);
        console.log('🔑 Token:', token);
        console.log('🌐 请求 URL:', `${BASE_URL}/api/mobile/profile/`);

        if (email && token) {
          const res = await fetch(`${BASE_URL}/api/mobile/profile/`, {
            headers: { Authorization: `Token ${token}` }
          });

          console.log('📬 响应状态码:', res.status);
            const text = await res.text();
            console.log('📝 响应原文内容:', text);

          if (!res.ok || !text.startsWith('{')) {
            console.warn('🧨 非 JSON 响应文本:', text);
            throw new Error('Invalid response');
          }

          const profile = JSON.parse(text);
          const role = profile?.role;
          console.log('✅ 成功解析 JSON:', profile);
          console.log('👤 用户角色:', profile?.user?.role);

          navigation.reset({
            index: 0,
            routes: [{ name: 'MainTabs', params: { role } }]
          });
        } else {
          navigation.replace('Login');
        }
      } catch (e) {
        console.warn('⚠️ 自动登录失败:', e);
        navigation.replace('Login');
      }
    };

    checkLogin();
  }, []);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <ActivityIndicator size="large" />
    </View>
  );
}
