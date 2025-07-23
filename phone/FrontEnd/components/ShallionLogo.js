// components/ShallionLogo.js
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';

export default function ShallionLogo({ width = 120, height = 60, position = true }) {
  return (
    <View style={[position ? styles.wrapper : null, { width, height }]}>
      <Image
        source={require('../assets/ShallionLogoTransparent.png')}
        style={styles.logo}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
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
});
