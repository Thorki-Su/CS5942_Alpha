import React, { useLayoutEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, ImageBackground, Dimensions } from 'react-native';
import { COLORS, TYPOGRAPHY } from '../styles/theme';

import LogoutButton from '../components/LogoutButton';

const screenWidth = Dimensions.get('window').width;

export default function HomeScreen({ navigation }) {
  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => <LogoutButton />,
    });
  }, [navigation]);
  return (
    <ScrollView contentContainerStyle={{ backgroundColor: COLORS.background, paddingBottom: 40 }}>
      {/* Hero Section */}
      <ImageBackground
        source={require('../assets/HeroImage.jpg')}
        style={styles.heroSection}
        resizeMode="cover"
      >
        <View style={styles.heroTextContainer}>
          <Text style={styles.heroTitle}>S H A L L I O N</Text>
          <Text style={TYPOGRAPHY.subtitle}>
            WHERE COMPASSION PEAKS AND SUPPORT PREVAILS
          </Text>
        </View>
      </ImageBackground>

      {/* Section */}
      <View style={styles.section}>
        <Text style={TYPOGRAPHY.paragraph}>
          Shallion Support is a bespoke support service dedicated to assisting individuals with autoimmune conditions such as M.E., Lupus, Fibromyalgia, and PTSD.
          <Text style={{ fontWeight: 'bold' }}> We provide non-medical, practical support to help you navigate your daily life with ease</Text>
          ,whether it's appointment management, housekeeping, pet care, planning and preparing your meals, so you can always have healthy and delicious options.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={TYPOGRAPHY.title}>Tailored Just for You</Text>
        <Text style={TYPOGRAPHY.paragraph}>
          At Shallion Support, we want to create a warm and supportive space
          <Text style={{ fontWeight: 'bold' }}> where you feel heard and valued.</Text>
          We are dedicated to understanding each person's unique challenges and tailoring our support to meet your needs. We're here to help!
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={TYPOGRAPHY.title}>What We Offer</Text>
        <Text style={styles.offerTitle}>Bespoke, Non-Medical Services</Text>
        <View style={styles.offerGrid}>
          <Text style={TYPOGRAPHY.paragraph}>• Personalized assistance with daily tasks and errands.</Text>
          <Text style={TYPOGRAPHY.paragraph}>• Organizing your weekly meals or a special gathering.</Text>
          <Text style={TYPOGRAPHY.paragraph}>• Helping navigate IT systems, direct debits, or health services.</Text>
        </View>
      </View>
      <View style={styles.section}>
        <View style={styles.offerGrid}>
          <Text style={TYPOGRAPHY.paragraph}>Shallion serves both paying clients and those who qualify for free services. We extend this support to individuals on
            <Text style={{ fontWeight: 'bold' }}> Personal Independence Payment (PIP) </Text>
            or with 
            <Text style={{ fontWeight: 'bold' }}> Limited Capability for Work </Text>
            through Universal Credit.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  heroSection: {
    width: screenWidth,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 18, 
  },
  heroTextContainer: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  heroTitle: {
    color: COLORS.white,
    fontSize: 36,
    fontFamily: 'serif',
    letterSpacing: 2,
    fontWeight: 'bold',
  },
  section: {
    paddingHorizontal: 20,
    paddingVertical: 18,
    maxWidth: 800,
    alignSelf: 'center',
  },
  offerTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginVertical: 18,
  },
  offerGrid: {
    gap: 5,
  },
});
