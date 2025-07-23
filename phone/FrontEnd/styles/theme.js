// styles/theme.js

export const COLORS = {
  background: '#F5F7FA',   // Alpha 网站背景色
  primary: '#007bff',      // 主色（按钮蓝）
  white: '#ffffff',
  black: '#000000',
  text: '#222222',
  secondaryText: '#555555',
  border: '#cccccc',
  error: '#ff4d4f',
  success: '#28a745',
};

export const TYPOGRAPHY = {
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 18,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    fontStyle: 'italic',
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 8,
    textAlign: 'center',
  },
  paragraph: {
    fontSize: 16,
    color: COLORS.text,
    lineHeight: 24,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.white,
    textAlign: 'center',
  },
};

export const INPUT_STYLE = {
  height: 48,
  borderColor: COLORS.border,
  borderWidth: 1,
  borderRadius: 8,
  marginBottom: 12,
  paddingHorizontal: 12,
  backgroundColor: COLORS.white,
};

export const BUTTON_STYLE = {
  backgroundColor: COLORS.primary,
  paddingVertical: 14,
  paddingHorizontal: 24,
  borderRadius: 8,
  alignItems: 'center',
  marginVertical: 10,
};

export const CONTAINER = {
  flex: 1,
  padding: 24,
  backgroundColor: COLORS.background,
  justifyContent: 'center',
};
export const scrollContainer = {
    padding: 24,
    paddingBottom: 80, // 防止最后一个输入框被遮挡
    backgroundColor: COLORS.background,
    flex: 1,
    justifyContent: 'center', // 让初始状态居中
};
