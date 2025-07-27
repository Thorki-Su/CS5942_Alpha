import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Alert,
  TouchableWithoutFeedback,
  Keyboard,
  TouchableOpacity,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import ShallionLogo from '../components/ShallionLogo';
import { COLORS, TYPOGRAPHY, INPUT_STYLE, BUTTON_STYLE } from '../styles/theme';
import { BASE_URL } from '../config';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Attention', 'Email or password cannot be empty.');
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/api/mobile/login/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // console.log("✅ Got token:", data.token);
        await AsyncStorage.setItem('userToken', data.token);
        await AsyncStorage.setItem('loggedInEmail', data.email);

        const current = await AsyncStorage.getAllKeys();
        console.log('📦 当前 AsyncStorage 所有键:', current);

        const role = data.role;  // ✅ 直接拿角色
        console.log('✅ 登录成功，跳转主页');

        navigation.reset({
          index: 0,
          routes: [{ name: 'MainTabs', params: { role } }],
        });
      } else {
        console.warn('登录失败:', data.error);
      }
    } catch (error) {
      console.error('请求失败:', error);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ShallionLogo />
        <Text style={[TYPOGRAPHY.title, { fontSize: 32, marginBottom: 32 }]}>Login</Text>

        <TextInput 
          style={INPUT_STYLE}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextInput 
          style={INPUT_STYLE}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity style={BUTTON_STYLE} onPress={handleLogin}>
          <Text style={TYPOGRAPHY.buttonText}>Sign In</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('RoleSelect')}>
          <View style={styles.linkContainer}>
            <Text>
              Don't have an account?{' '}
              <Text style={{ color: COLORS.primary, textAlign: 'center' }}>
                Register here
              </Text>
            </Text>
          </View>
        </TouchableOpacity>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    padding: 24,
  },
  linkContainer: {
    marginTop: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
