import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

import ShallionLogo from '../../components/ShallionLogo';
import { COLORS, TYPOGRAPHY, BUTTON_STYLE } from '../../styles/theme';

export default function RoleSelectScreen({ navigation }) {
  const handleSelectRole = (role) => {
    if (role === 'client') {
      navigation.navigate('ClientRegister');
    } else if (role === 'volunteer') {
      navigation.navigate('VolunteerRegister');
    }
  };

  return (
    <View style={styles.container}>
      {/* logo */}<ShallionLogo />
      <Text style={[TYPOGRAPHY.title, { fontSize: 28, marginBottom: 24 }]}>
        Choose your character
      </Text>

      {/* Role Selection Row */}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', width: '100%' }}>
        {/* Client Card */}
        <TouchableOpacity style={styles.card} onPress={() => handleSelectRole('client')}>
          <Image
            source={require('../../assets/administrative-help-template.jpg')} // 占位图
            style={styles.cardImage}
            // resizeMode="cover"
          />
          <Text style={styles.cardText}>I am a client</Text>
        </TouchableOpacity>

        {/* Volunteer Card */}
        <TouchableOpacity style={styles.card} onPress={() => handleSelectRole('volunteer')}>
          <Image
            source={require('../../assets/companionship-support-template.jpg')} // 占位图
            style={styles.cardImage}
            // resizeMode="cover"
          />
          <Text style={styles.cardText}>I am a volunteer</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'flex-start',
    alignItems: 'center',
    padding: 24,
    paddingTop: 200,
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
  card: {
  flex: 1,
  marginHorizontal: 8,
  borderRadius: 10,
  backgroundColor: '#fff',
  overflow: 'hidden',
  elevation: 3,
},
cardImage: {
  width: '100%',
  height: 180,
  aspectRatio: 1, // 保持横向长图比例（可根据图形微调，如 1.6 / 1.3）
  resizeMode: 'contain',
},
cardText: {
  paddingVertical: 12,
  textAlign: 'center',
  fontSize: 16,
  fontWeight: 'bold',
  color: '#007bff',
  backgroundColor: '#F5F7FA',
},
});
