import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';

const CollapsibleMultiSelect = ({ label, options, selected, onChange }) => {
  const [expanded, setExpanded] = useState(false);

  const toggleOption = (item) => {
    if (selected.includes(item)) {
      onChange(selected.filter(i => i !== item));
    } else {
      onChange([...selected, item]);
    }
  };

  return (
    <View style={{ marginBottom: 15 }}>
      <TouchableOpacity onPress={() => setExpanded(!expanded)}>
        <Text style={{ fontWeight: 'bold', marginBottom: 5 }}>
          {label} {expanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={{ paddingLeft: 10 }}>
          {options.map((item) => (
            <TouchableOpacity
              key={item}
              onPress={() => toggleOption(item)}
              style={{
                padding: 8,
                backgroundColor: selected.includes(item) ? '#d0f0c0' : '#eee',
                borderRadius: 5,
                marginBottom: 5,
              }}
            >
              <Text>{item}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
};

export default CollapsibleMultiSelect;
