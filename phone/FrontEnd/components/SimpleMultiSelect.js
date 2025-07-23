import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';

const SimpleMultiSelect = ({ label, options, selected, onChange }) => {
  const toggleOption = (item) => {
    if (selected.includes(item)) {
      onChange(selected.filter(i => i !== item));
    } else {
      onChange([...selected, item]);
    }
  };

  return (
    <View style={{ marginBottom: 15 }}>
      <Text style={{ fontWeight: 'bold', marginBottom: 5 }}>{label}</Text>
      {options.map((item) => (
        <TouchableOpacity
          key={item}
          onPress={() => toggleOption(item)}
          style={{
            padding: 10,
            backgroundColor: selected.includes(item) ? '#aef' : '#eee',
            marginVertical: 5,
            borderRadius: 5,
          }}
        >
          <Text>{item}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

export default SimpleMultiSelect;
