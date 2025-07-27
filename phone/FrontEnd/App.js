import React, { useEffect, useState ,Fragment} from 'react';
import { NavigationContainer,useRoute} from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActionSheetProvider } from '@expo/react-native-action-sheet';
import Toast, { BaseToast, ErrorToast } from 'react-native-toast-message';
import { toastConfig } from './components/ToastConfig';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator } from 'react-native';
import {BASE_URL} from './config'
// js.files import below
import StartupScreen from './screens/StartupScreen';
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

import ClientTaskListScreen from './task/ClientTaskListScreen';
import CreateTaskScreen from './task/CreateTaskScreen';
import ClientTaskConfirmScreen from './task/ClientTaskConfirmScreen';
import ClientSubmitFeedbackScreen from './task/ClientSubmitFeedbackScreen';
import VolunteerTaskListScreen from './task/VolunteerTaskListScreen';
import VolunteerMyApplicationsScreen from './task/VolunteerMyApplicationsScreen';
import VolunteerApplicationDetailScreen from './task/VolunteerApplicationDetailScreen';
import VolunteerSubmitRecordScreen from './task/VolunteerSubmitRecordScreen';
import VolunteerSubmitFeedbackScreen from './task/VolunteerSubmitFeedbackScreen';
import TaskDetailScreen from './task/TaskDetailScreen';
import TaskApplicationListScreen from './task/TaskApplicationListScreen';

import SettingsScreen from './screens/SettingsScreen';

import ChangePasswordScreen from './screens/ChangePasswordScreen';


// PageToPage Stack
const Stack = createNativeStackNavigator();
// Bottom Tab
const Tab = createBottomTabNavigator();

function MainTabs({}) {
  const route = useRoute();
  const role = route.params?.role;

  console.log('✅ ROLE in MainTabs:', role);

  return (
    <Tab.Navigator>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />

      {/* ✅ 只有 client 显示 client 的任务列表 */}
      {role === 'client' && (
        <Tab.Screen name="Tasks" component={ClientTaskListScreen} />
      )}

      {/* ✅ 只有志愿者角色才显示 Tasks 页签 */}
      {role === 'volunteer' && (
        <Tab.Screen name="Tasks" component={VolunteerTaskListScreen} />
      )}
      {role === 'volunteer' && (
        <Tab.Screen name="MyApplications" component={VolunteerMyApplicationsScreen} /> 
      )}
      <Tab.Screen name="Profile" component={ProfileDetailScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  console.log("🌀 App 启动了！");
  const [initialRoute, setInitialRoute] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return (
    <ActionSheetProvider>
      <Fragment>
        <NavigationContainer>
          <Stack.Navigator initialRouteName="Startup" screenOptions={{ headerShown: true }}>
            <Stack.Screen name="Startup" component={StartupScreen} options={{ headerShown: false }} />
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
            <Stack.Screen name="ClientTaskList" component={ClientTaskListScreen} />
            <Stack.Screen name="CreateTask" component={CreateTaskScreen} />
            <Stack.Screen name="ClientSubmitFeedback" component={ClientSubmitFeedbackScreen} />
            <Stack.Screen name="ClientTaskConfirm" component={ClientTaskConfirmScreen} />
            <Stack.Screen name="VolunteerTaskListScreen" component={VolunteerTaskListScreen} />
						<Stack.Screen name="VolunteerMyApplicationsScreen" component={VolunteerMyApplicationsScreen} />
						<Stack.Screen name="VolunteerApplicationDetail" component={VolunteerApplicationDetailScreen} options={{ title: 'Application Detail' }} />
            <Stack.Screen name="VolunteerSubmitRecord" component={VolunteerSubmitRecordScreen} />
						<Stack.Screen name="VolunteerSubmitFeedback" component={VolunteerSubmitFeedbackScreen} />
            <Stack.Screen name="TaskDetail" component={TaskDetailScreen} />
            <Stack.Screen name="TaskApplications" component={TaskApplicationListScreen} options={{ title: 'Applications' }}/>
            {/* stack请在此行之上添加 */}
          </Stack.Navigator>
        </NavigationContainer>

        {/* Toast 必须放在底部 */}
        <Toast config={toastConfig} />
      </Fragment>
    </ActionSheetProvider>
  );
}
