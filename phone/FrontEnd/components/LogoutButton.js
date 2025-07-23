import React from 'react';
import { TouchableOpacity, Text, Alert,style } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';

export default function LogoutButton() {
  const navigation = useNavigation();

  const handleLogout = async () => {
    Alert.alert(
      'Confirm Logout',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('loggedInEmail');
            await AsyncStorage.removeItem('userToken');
            await AsyncStorage.removeItem('userData');
            await AsyncStorage.clear();
            console.log('🧼 Storage cleared.');
            navigation.reset({
              index: 0,
              routes: [{ name: 'Login' }],
            });
          },
        },
      ]
    );
  };

  return (
    <TouchableOpacity onPress={handleLogout} style={[defaultStyle, style]}>
      <Text style={{ color: 'red' }}>Logout</Text>
    </TouchableOpacity>
  );
}

const defaultStyle = {
  marginRight: 16
};