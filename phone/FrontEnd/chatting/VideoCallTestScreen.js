// screens/VideoCallTestScreen.js

import React, { useEffect, useRef } from 'react';
import { View, Text, Button, StyleSheet, Alert } from 'react-native';
import { WS_URL } from '../config';

import { getVideoCallRoomURL } from '../constants/wsRoutes';

const VideoCallTestScreen = ({ route }) => {
  console.log("🔍 Route params:", route?.params);
  const ws = useRef(null);
  const roomName = `task-${application.task_id}`;
  const myUserId = route?.params?.userId || 1;
  const targetUserId = route?.params?.targetId || 2;

  const sendHangup = () => {
  if (ws.current) {
    ws.current.send(JSON.stringify({
      type: "hangup",
      from: myUserId,
      to: targetUserId,
    }));
  }
};

  useEffect(() => {
    ws.current = new WebSocket(getVideoCallRoomURL(roomName));
    ws.current.onopen = () => {
        console.log("🔌 WebSocket connected");
    };

    ws.current.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log("📩 Received:", data);

        if (data.type === "call_offer") {
            Alert.alert("📞 视频呼叫", `来自用户 ${data.from}`);
        }

        if (data.type === "hangup") {
            Alert.alert("📴 通话结束", "对方已挂断");
        }
    };

    ws.current.onerror = (e) => console.log("❌ WebSocket error:", e.message);
    ws.current.onclose = () => console.log("❎ WebSocket closed");

    return () => {
      ws.current?.close();
    };
  }, []);



  return (
    <View style={styles.container}>
      <Text style={styles.title}>WebSocket Test Room</Text>
      <Button
        title="Send Hangup"
        onPress={sendHangup}
      />
    </View>
  );
};

export default VideoCallTestScreen;

const styles = StyleSheet.create({
  container: {
    flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff'
  },
  title: {
    fontSize: 24, fontWeight: 'bold', marginBottom: 20
  }
});
