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
  Modal,
  TouchableOpacity,
} from 'react-native';
import Checkbox from 'expo-checkbox';
import { Picker } from '@react-native-picker/picker';
import { useNavigation } from '@react-navigation/native';
import ShallionLogo from '../../components/ShallionLogo';
import { COLORS, TYPOGRAPHY, INPUT_STYLE, BUTTON_STYLE } from '../../styles/theme';
import { BASE_URL } from '../../config';
import axios from 'axios';

const VolunteerRegisterScreen = () => {
  const navigation = useNavigation();
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password1: '',
    password2: '',
    phone_number: '',
    university_course: '',
    profession: '',
    location: '',
    is_for_credit: '',
    consent_safeguard: false,
  });

  const [loading, setLoading] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    const {
      email, first_name, last_name, password1, password2,
      phone_number, university_course, profession, location,
      is_for_credit, consent_safeguard,
    } = formData;

    if (!email || !first_name || !last_name || !password1 || !password2 || !phone_number || !university_course || !profession || !location || is_for_credit === '') {
      Alert.alert('Attention', 'Please fill in all required fields.');
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
      const response = await axios.post(`${BASE_URL}/register/volunteer/`, {
        ...formData,
        is_for_credit: is_for_credit === 'Yes'
      });

      if (response.status === 200) {
        Alert.alert('Registration Successful', 'Welcome, volunteer!');
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
          <Text style={[TYPOGRAPHY.title, { fontSize: 24, marginTop: 80, marginBottom: 24 }]}>Register as Volunteer</Text>

          <Text style={styles.label}>1. Email:</Text>
          <TextInput style={INPUT_STYLE} keyboardType="email-address" value={formData.email} onChangeText={t => handleChange('email', t)} />

          <Text style={styles.label}>2. First Name:</Text>
          <TextInput style={INPUT_STYLE} value={formData.first_name} onChangeText={t => handleChange('first_name', t)} />

          <Text style={styles.label}>3. Last Name:</Text>
          <TextInput style={INPUT_STYLE} value={formData.last_name} onChangeText={t => handleChange('last_name', t)} />

          <Text style={styles.label}>4. Password:</Text>
          <TextInput style={INPUT_STYLE} secureTextEntry value={formData.password1} onChangeText={t => handleChange('password1', t)} />

          <Text style={styles.label}>5. Confirm Password:</Text>
          <TextInput style={INPUT_STYLE} secureTextEntry value={formData.password2} onChangeText={t => handleChange('password2', t)} />

          <Text style={styles.label}>6. Phone Number:</Text>
          <TextInput style={INPUT_STYLE} keyboardType="phone-pad" value={formData.phone_number} onChangeText={t => handleChange('phone_number', t)} />

          <Text style={styles.label}>7. University and Major:</Text>
          <TextInput style={INPUT_STYLE} value={formData.university_course} onChangeText={t => handleChange('university_course', t)} />

          <Text style={styles.label}>8. Profession:</Text>
          <TextInput style={INPUT_STYLE} value={formData.profession} onChangeText={t => handleChange('profession', t)} />

          <Text style={styles.label}>9. Postcode:</Text>
          <TextInput style={INPUT_STYLE} value={formData.location} onChangeText={t => handleChange('location', t)} />

          <Text style={styles.label}>10. Are you volunteering for credit?</Text>
          <TouchableOpacity
            onPress={() => setShowCreditModal(true)}
            style={[INPUT_STYLE, { justifyContent: 'center' }]}
          >
            <Text>{formData.is_for_credit || 'Select Yes or No'}</Text>
          </TouchableOpacity>

          <Modal visible={showCreditModal} transparent animationType="fade">
            <TouchableOpacity style={styles.modalBackdrop} onPress={() => setShowCreditModal(false)}>
              <View style={styles.modalPicker}>
                <TouchableOpacity onPress={() => { handleChange('is_for_credit', 'Yes'); setShowCreditModal(false); }}><Text style={styles.modalItem}>Yes</Text></TouchableOpacity>
                <TouchableOpacity onPress={() => { handleChange('is_for_credit', 'No'); setShowCreditModal(false); }}><Text style={styles.modalItem}>No</Text></TouchableOpacity>
              </View>
            </TouchableOpacity>
          </Modal>

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
        </ScrollView>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
};

export default VolunteerRegisterScreen;

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
  checkboxWrapper: {
    flexDirection: 'row',
    marginVertical: 16,
  },
  modalBackdrop: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  modalPicker: {
    backgroundColor: '#fff',
    marginHorizontal: 40,
    padding: 20,
    borderRadius: 8,
  },
  modalItem: {
    fontSize: 18,
    paddingVertical: 10,
    textAlign: 'center',
  },
});
