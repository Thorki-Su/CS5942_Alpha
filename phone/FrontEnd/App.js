import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator } from 'react-native';
// js.files import below
import LoginScreen from './screens/LoginScreen';
import HomeScreen from './screens/HomeScreen';

import RegisterRoleSelectScreen from './screens/register/RegisterRoleSelectScreen';
import ClientRegisterScreen from './screens/register/ClientRegisterScreen';
import VolunteerRegisterScreen from './screens/register/VolunteerRegisterScreen';

import ProfileDetailScreen from './screens/profile/ProfileDetailScreen';
import EditClientProfileScreen from './screens/profile/EditClientProfileScreen';
import EditVolunteerProfileScreen from './screens/profile/EditVolunteerProfileScreen';
import UploadAvatarScreen from './screens/profile/UploadAvatarScreen';
import EditPreferredTimesScreen from './screens/profile/EditPreferredTimesScreen';

import SettingsScreen from './screens/SettingsScreen';

import ChangePasswordScreen from './screens/ChangePasswordScreen';
import UserProfileScreen from './screens/UserProfileScreen';

// PageToPage Stack
const Stack = createNativeStackNavigator();
// Bottom Tab
const Tab = createBottomTabNavigator();
function MainTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="首页" component={HomeScreen} />
      <Tab.Screen name="设置" component={SettingsScreen} />
      <Tab.Screen name="我的" component={ProfileDetailScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [initialRoute, setInitialRoute] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkLogin = async () => {
      try {
        const user = await AsyncStorage.getItem('loggedInEmail');
        console.log('已保存的用户名是：', user);
        if (user) {
          setInitialRoute('MainTabs'); // 有记录就跳主页
        } else {
          setInitialRoute('Login'); // 没有就跳登录
        }
      } catch (e) {
        setInitialRoute('Login');
      }finally {
      setIsLoading(false); // 不管怎样都结束加载
      }
    };checkLogin();
    }, []);
    

  if (!initialRoute) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (isLoading || !initialRoute) return null; // 或者加载动画

  return (
    <NavigationContainer>
    <Stack.Navigator initialRouteName={initialRoute} screenOptions={{ headerShown: true }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="RoleSelect" component={RegisterRoleSelectScreen} />
      <Stack.Screen name="ClientRegister" component={ClientRegisterScreen} />
      <Stack.Screen name="VolunteerRegister" component={VolunteerRegisterScreen} />
      <Stack.Screen name="MainTabs" component={MainTabs} options={{ headerShown: false }} />
      <Stack.Screen name="EditClientProfile" component={EditClientProfileScreen} />
      <Stack.Screen name="EditVolunteerProfile" component={EditVolunteerProfileScreen} options={{ title: 'Edit Volunteer Profile' }}/>
      <Stack.Screen name="UploadAvatarScreen" component={UploadAvatarScreen} />
      <Stack.Screen name="EditPreferredTimes" component={EditPreferredTimesScreen} />
      <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} options={{ title: "修改密码", headerBackTitle: "返回" }} />
    </Stack.Navigator>
    </NavigationContainer>
    
  );
}
