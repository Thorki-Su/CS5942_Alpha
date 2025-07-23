import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { BASE_URL } from '../config';

/**
 * 拉取当前登录用户的 Profile 信息（用于 EditProfile 页面）
 * @returns {Promise<object|null>} 用户信息或 null（拉取失败）
 */
export const fetchUserProfile = async () => {
  try {
    const token = await AsyncStorage.getItem('userToken');
    if (!token) {
      console.warn('⚠️ 未找到 Token,无法拉取用户信息');
      return null;
    }

    const response = await axios.get(`${BASE_URL}/api/mobile/profile/`, {
      headers: {
        Authorization: `Token ${token}`,
      },
    });
    console.log('📥 成功取到的 profile 数据');
    // console.log('📥 拉取到的 profile 数据:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ 拉取用户信息失败:', error.response?.data || error.message);
    return null;
  }
};

export default fetchUserProfile;