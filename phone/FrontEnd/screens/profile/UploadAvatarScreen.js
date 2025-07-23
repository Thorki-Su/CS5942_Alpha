import React, { useState } from 'react';
import { View, Text, Button, Image, StyleSheet, ActivityIndicator, Alert,TouchableOpacity } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BASE_URL } from '../../config';
import { useNavigation } from '@react-navigation/native';

export default function UploadAvatarScreen() {
  const [imageUri, setImageUri] = useState(null);
  const [uploading, setUploading] = useState(false);
  const navigation = useNavigation();

  const pickFromLibrary = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
      base64: true,
    });

    if (!result.cancelled) {
      setImageUri(result.uri);
      uploadToServer(result);
    }
  };

  const takePhoto = async () => {
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
      base64: true,
    });

    if (!result.cancelled) {
      setImageUri(result.uri);
      uploadToServer(result);
    }
  };

  const uploadToServer = async (imageResult) => {
    setUploading(true);
    try {
      const token = await AsyncStorage.getItem('token');
      const res = await fetch(`${BASE_URL}/api/mobile/upload_avatar/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Token ${token}`,
        },
        body: JSON.stringify({
          cropped_image_data: `data:image/jpeg;base64,${imageResult.base64}`,
        }),
      });

      if (res.ok) {
        Alert.alert('✅ 上传成功');
        navigation.navigate('ProfileDetailScreen', { refreshAvatar: true }); // 返回profile
      } else {
        Alert.alert('❌ 上传失败');
      }
    } catch (error) {
      Alert.alert('❌ 网络错误', error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Upload Your Avatar</Text>
      <Button title="📸 拍照上传" onPress={takePhoto} />
      <View style={{ height: 10 }} />
      <Button title="🖼 从相册选择" onPress={pickFromLibrary} />
      <TouchableOpacity onPress={pickFromLibrary} activeOpacity={0.8}>
			<View style={styles.avatarContainer}>
					{imageUri ? (
					<Image source={{ uri: imageUri }} style={styles.avatarImage} />
					) : (
					<Text style={{ color: '#888' }}>点击上传头像</Text>
					)}
			</View>
			</TouchableOpacity>
      {uploading && <ActivityIndicator size="large" />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    marginBottom: 20,
  },
  avatar: {
    width: 200,
    height: 200,
    marginTop: 20,
    borderRadius: 100,
  },
});
