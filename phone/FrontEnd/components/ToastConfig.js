import React from 'react';
import { BaseToast, ErrorToast } from 'react-native-toast-message';

const commonStyle = {
  borderLeftWidth: 5,
  borderRadius: 8,
  backgroundColor: 'white',
  width: '85%',
  alignSelf: 'center',
  position: 'absolute',
  top: '40%', // 居中显示
  shadowColor: '#000',
  shadowOpacity: 0.1,
  shadowOffset: { width: 0, height: 2 },
  shadowRadius: 6,
  elevation: 3,
};

export const toastConfig = {
  success: (props) => (
    <BaseToast
      {...props}
      style={{
        ...commonStyle,
        borderLeftColor: '#4CAF50', // 成功绿色
      }}
      contentContainerStyle={{ paddingHorizontal: 15 }}
      text1Style={{
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
      }}
    />
  ),
  error: (props) => (
    <ErrorToast
      {...props}
      style={{
        ...commonStyle,
        borderLeftColor: '#FF3B30', // 错误红色
      }}
      contentContainerStyle={{ paddingHorizontal: 15 }}
      text1Style={{
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
      }}
    />
  ),
};
