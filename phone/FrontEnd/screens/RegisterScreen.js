import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Image,
  TouchableWithoutFeedback,
  Keyboard,
  Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import ShallionLogo from '../components/ShallionLogo';
import { COLORS, TYPOGRAPHY, INPUT_STYLE, BUTTON_STYLE } from '../styles/theme';

export default function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleRegister = async () => {
    if (!username || !password || !confirmPassword) {
      Alert.alert('请填写完整信息');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('两次输入密码不一致');
      return;
    }

    try {
      // 获取已有用户
      const usersData = await AsyncStorage.getItem('users');
      const users = usersData ? JSON.parse(usersData) : {};

      if (users[username]) {
        Alert.alert('用户名已存在');
        return;
      }

      // 存储新用户
      users[username] = password;
      await AsyncStorage.setItem('users', JSON.stringify(users));
      await AsyncStorage.setItem('loggedInUser', username);
      Alert.alert('注册成功');
      navigation.navigate('MainTabs');
    } catch (e) {
      console.error('注册失败', e);
      Alert.alert('注册失败，请重试');
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* logo */}<ShallionLogo />
        <Text style={[TYPOGRAPHY.title, { fontSize: 32, marginBottom: 32 }]}>Register</Text>

        <TextInput
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          style={INPUT_STYLE}
        />
        <TextInput
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={INPUT_STYLE}
        />
        <TextInput
          placeholder="Comfirm Password"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
          style={INPUT_STYLE}
        />

        <TouchableOpacity style={BUTTON_STYLE} onPress={handleRegister}>
          <Text style={TYPOGRAPHY.buttonText}>Register</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.linkContainer}>
          <Text>
            Have an account already?<Text style={{ color: COLORS.primary }}> Sign in here!</Text>
          </Text>
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
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    alignSelf: 'center',
    marginBottom: 32,
    color: '#222',
  },
  logoWrapper: {
    position: 'absolute',
    top: 20,
    left: 20,
    width: 120,
    height: 60,
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  linkContainer: {
    marginTop: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
