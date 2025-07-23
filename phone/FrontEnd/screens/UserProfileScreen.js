import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, Alert,KeyboardAvoidingView, Platform, ScrollView,StyleSheet,TouchableWithoutFeedback,Keyboard} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import ShallionLogo from '../components/ShallionLogo';

export default function UserProfileScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [nickname, setNickname] = useState('');
  const [signature, setSignature] = useState('');

  // 加载本地存储的昵称和签名
  useEffect(() => {
    const fetchUserInfo = async () => {
      const name = await AsyncStorage.getItem('loggedInUser');
      const nick = await AsyncStorage.getItem('nickname');
      const sign = await AsyncStorage.getItem('signature');
      setUsername(name || '');
      setNickname(nick || '');
      setSignature(sign || '');
    };
  fetchUserInfo();
  }, []);

	const handleSave = async () => {
    try {
      await AsyncStorage.setItem('nickname', nickname);
      await AsyncStorage.setItem('signature', signature);
			console.log('个人信息已更新',nickname)
			console.log('个人信息已更新',signature)
      Alert.alert('保存成功', '个人信息已更新');
    } catch (e) {
			console.log('个人信息更新失败',e)
      Alert.alert('保存失败', '请重试');
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('loggedInEmail');
    await AsyncStorage.removeItem('userData');
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  // 注销账户，清除所有关联数据
  const handleDeleteAccount = async () => {
    try {
      const currentUser = await AsyncStorage.getItem('loggedInUser');

      if (currentUser) {
        const usersStr = await AsyncStorage.getItem('users');
        const users = usersStr ? JSON.parse(usersStr) : {};

        delete users[currentUser];

        await AsyncStorage.setItem('users', JSON.stringify(users));

        await AsyncStorage.multiRemove([
          'loggedInUser',
          'nickname',
          'signature',
        ]);
        console.log(`✅ 用户 ${currentUser} 数据已全部清除`);
        navigation.navigate('Login');
      }
    } catch (err) {
      console.error('注销出错:', err);
      Alert.alert('注销失败，请重试');
    }
  };

  const confirmDelete = () => {
    Alert.alert(
      '确认注销',
      '该操作将永久删除当前账户数据，是否继续？',
      [
        { text: '取消', style: 'cancel' },
        { text: '确认注销', style: 'destructive', onPress: handleDeleteAccount },
      ]
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <Text style={styles.title}>用户资料</Text>

        <Text style={styles.label}>用户名（不可修改）</Text>
        <TextInput
          value={username}
          editable={false}
          style={styles.input}
        />

        <Text style={styles.label}>昵称</Text>
        <TextInput
          style={styles.input}
          value={nickname}
          onChangeText={setNickname}
          placeholder="输入昵称"
        />

        <Text style={styles.label}>签名</Text>
        <TextInput
          style={[styles.input, { height: 80 }]}
          value={signature}
          onChangeText={setSignature}
          placeholder="输入个性签名"
          multiline
        />
        <View style={{ marginTop: 20 }}>
          <View style={{ height: 10 }} />
          <Button title="保存" onPress={handleSave} />
        </View>
        <Button title="注销账户（清除所有数据）" color="red" onPress={confirmDelete} />
        <Button title="退出登录" onPress={handleLogout} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  inner: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 24,
    alignSelf: 'center',
  },
  label: {
    fontSize: 16,
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    borderRadius: 6,
    backgroundColor: '#fff',
  },
});