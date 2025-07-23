import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  Alert,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  TouchableOpacity,
  Modal,
} from 'react-native';

import Checkbox from 'expo-checkbox';
import { useNavigation } from '@react-navigation/native';
import axios from 'axios';

import ShallionLogo from '../../components/ShallionLogo';
import { COLORS, TYPOGRAPHY, INPUT_STYLE, BUTTON_STYLE } from '../../styles/theme';
import { BASE_URL } from '../../config';

const ClientRegisterScreen = () => {
  const navigation = useNavigation();

  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password1: '',
    password2: '',
    phone_number: '',
    location: '',
    preferred_contact_method: '',
    consent_safeguard: false,
    certifications: [],
  });

  const [loading, setLoading] = useState(false);
  const [certifications, setCertifications] = useState([]);
  const [showPicker, setShowPicker] = useState(false);
  const contactOptions = ['Email', 'Phone'];

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const toggleCertification = (item) => {
    setCertifications(prev =>
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  const handleSubmit = async () => {
    const {
      email, first_name, last_name, password1, password2,
      phone_number, location, preferred_contact_method, consent_safeguard,
    } = formData;

    if (!email || !first_name || !last_name || !password1 || !password2 || !phone_number || !location || !preferred_contact_method) {
      Alert.alert('Attention', 'Please fill in all the required fields.');
      return;
    }

    if (password1 !== password2) {
      Alert.alert('Attention', 'Passwords do not match.');
      return;
    }

    if (!consent_safeguard) {
      Alert.alert('Attention', 'You must agree to the safeguard policy.');
      return;
    }

    try {
      setLoading(true);
      const submissionData = {
        ...formData,
        certifications,
      };
      const response = await axios.post(`${BASE_URL}/register/client/`, submissionData);

      if (response.status === 200) {
        Alert.alert('Registration Successful', 'Welcome, client!');
        navigation.navigate('Login');
      }
    } catch (error) {
      const msg = error.response?.data?.error || 'Something went wrong.';
      Alert.alert('Registration Failed', msg);
      console.error('Registration Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 0}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <ShallionLogo />
          <View style={{ marginTop: 100 }}>
            <Text style={[TYPOGRAPHY.title, { fontSize: 24, marginBottom: 24 }]}>Register as Client</Text>

            <Text style={styles.label}>1. Email:</Text>
            <TextInput style={INPUT_STYLE} keyboardType="email-address" value={formData.email} onChangeText={t => handleChange('email', t)} />

            <Text style={styles.label}>2. First Name:</Text>
            <TextInput style={INPUT_STYLE} value={formData.first_name} onChangeText={t => handleChange('first_name', t)} />

            <Text style={styles.label}>3. Last Name:</Text>
            <TextInput style={INPUT_STYLE} value={formData.last_name} onChangeText={t => handleChange('last_name', t)} />

            <Text style={styles.label}>4. Password:</Text>
            <TextInput style={INPUT_STYLE} secureTextEntry value={formData.password1} onChangeText={t => handleChange('password1', t)} />
            <Text style={styles.hint}>Password must be 8+ characters, not too simple, and not all digits.</Text>

            <Text style={styles.label}>5. Confirm Password:</Text>
            <TextInput style={INPUT_STYLE} secureTextEntry value={formData.password2} onChangeText={t => handleChange('password2', t)} />

            <Text style={styles.label}>6. Phone Number:</Text>
            <TextInput style={INPUT_STYLE} keyboardType="phone-pad" value={formData.phone_number} onChangeText={t => handleChange('phone_number', t)} />

            <Text style={styles.label}>7. Contact Preference:</Text>
            <TouchableOpacity 
            style={styles.pickerTouchable}
            onPress={() => setShowPicker(true)}
            >
              <Text style={styles.pickerText}>
                {formData.preferred_contact_method || 'Select Contact Preference'}
              </Text>
            </TouchableOpacity>

            <Modal
              visible={showPicker}
              transparent
              animationType="fade"
              onRequestClose={() => setShowPicker(false)}
            >
              <TouchableOpacity
                style={styles.modalOverlay}
                activeOpacity={1}
                onPress={() => setShowPicker(false)}
              >
                <View style={styles.modalPickerContainer}>
                  <TouchableOpacity onPress={() => {
                    handleChange('preferred_contact_method', 'Email');
                    setShowPicker(false);
                  }}>
                    <Text style={styles.modalPickerItem}>Email</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => {
                    handleChange('preferred_contact_method', 'Phone');
                    setShowPicker(false);
                  }}>
                    <Text style={styles.modalPickerItem}>Phone</Text>
                  </TouchableOpacity>
                </View>
              </TouchableOpacity>
            </Modal>
            <Text style={styles.label}>8. Location (Postcode or Address):</Text>
            <TextInput style={INPUT_STYLE} value={formData.location} onChangeText={t => handleChange('location', t)} />
            <TouchableOpacity onPress={() => Alert.alert('Info', 'Auto-location not implemented yet.')}>
              <Text style={{ color: COLORS.primary, marginBottom: 8 }}>📍 Use My Location</Text>
            </TouchableOpacity>

            <Text style={styles.label}>9. Certifications (You can choose multiple):</Text>
            <View style={styles.certificationRow}>
              {['PIP', 'ADP', 'LWC'].map(cert => (
                <View key={cert} style={styles.certItem}>
                  <Checkbox
                    value={(formData.certifications || []).includes(cert)}
                    onValueChange={(val) => {
                      const newCerts = val
                        ? [...formData.certifications, cert]
                        : formData.certifications.filter(c => c !== cert);
                      handleChange('certifications', newCerts);
                    }}
                  />
                  <Text style={{ marginLeft: 6 }}>{cert}</Text>
                </View>
              ))}
            </View>
            <View style={styles.checkboxWrapper}>
              <Text style={{ marginLeft: 8 }}>
                I agree with the agreement: 
              </Text>
              <Checkbox
                value={formData.consent_safeguard}
                onValueChange={val => handleChange('consent_safeguard', val)}
                color={formData.consent_safeguard ? COLORS.primary : undefined}
              />
            </View>
            <Button
              title={loading ? 'Registering...' : 'Register'}
              onPress={handleSubmit}
              disabled={loading}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
};

export default ClientRegisterScreen;

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: COLORS.background,
    padding: 24,
  },
  label: {
    fontSize: 16,
    marginTop: 12,
    marginBottom: 4,
  },
  hint: {
    fontSize: 12,
    color: 'gray',
    marginBottom: 8,
  },
  checkboxWrapper: {
    marginVertical: 16,
  },
  pickerContainer: {
    backgroundColor: '#fff',
    borderRadius: 6,
    padding: 10,
    elevation: 5,
    marginBottom: 12,
  },
  pickerOption: {
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: '#ccc',
  },
  pickerTouchable: {
  ...INPUT_STYLE,
  justifyContent: 'center',
},
pickerText: {
  fontSize: 16,
  color: '#333',
},
modalOverlay: {
  flex: 1,
  backgroundColor: 'rgba(0,0,0,0.3)',
  justifyContent: 'center',
  alignItems: 'center',
},
modalPickerContainer: {
  backgroundColor: '#fff',
  borderRadius: 10,
  padding: 20,
  width: 250,
},
modalPickerItem: {
  fontSize: 18,
  paddingVertical: 10,
  textAlign: 'center',
},
checkboxWrapper: {
  flexDirection: 'row',
  alignItems: 'center',
  marginTop: 16,
},
certificationRow: {
  flexDirection: 'row',
  justifyContent: 'space-between',
  marginTop: 8,
  marginBottom: 20,
},
certItem: {
  flexDirection: 'row',
  alignItems: 'center',
},
});
