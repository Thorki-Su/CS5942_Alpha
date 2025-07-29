// phone/FrontEnd/chatting/VideoCallScreen.js
import React, { useEffect, useRef, useState } from 'react';
import { useRoute } from '@react-navigation/native';
import { View, Button, StyleSheet } from 'react-native';
// import { RTCPeerConnection, RTCView, mediaDevices } from 'react-native-webrtc';

import { WS_URL } from '../config';

export default function VideoCallScreen() {
	const route = useRoute(); // ✅ 移到组件内部
  const { taskId } = route.params;
  const SIGNAL_SERVER = `${WS_URL}/ws/video/task-${taskId}/`;

  const ws = useRef(null);
  const pc = useRef(new RTCPeerConnection());
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);

  // 初始化摄像头与 WebSocket
  useEffect(() => {
    (async () => {
      const stream = await mediaDevices.getUserMedia({
        audio: true,
        video: true,
      });
      setLocalStream(stream);
      stream.getTracks().forEach(track => pc.current.addTrack(track, stream));
    })();

    ws.current = new WebSocket(SIGNAL_SERVER);

    ws.current.onmessage = async ({ data }) => {
      const msg = JSON.parse(data);
      if (msg.type === 'offer') {
        await pc.current.setRemoteDescription(msg);
        const answer = await pc.current.createAnswer();
        await pc.current.setLocalDescription(answer);
        ws.current.send(JSON.stringify(answer));
      } else if (msg.type === 'answer') {
        await pc.current.setRemoteDescription(msg);
      } else if (msg.type === 'candidate') {
        try {
          await pc.current.addIceCandidate(msg.candidate);
        } catch (e) {
          console.error('Error adding ICE candidate:', e);
        }
      }
    };

    pc.current.onicecandidate = (event) => {
      if (event.candidate) {
        ws.current.send(JSON.stringify({ type: 'candidate', candidate: event.candidate }));
      }
    };

    pc.current.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        setRemoteStream(event.streams[0]);
      }
    };

    return () => {
      ws.current?.close();
      pc.current.close();
      localStream?.getTracks().forEach(t => t.stop());
    };
  }, []);

  const startCall = async () => {
    const offer = await pc.current.createOffer();
    await pc.current.setLocalDescription(offer);
    ws.current.send(JSON.stringify(offer));
  };

  return (
    <View style={styles.container}>
      {localStream && (
        <RTCView
          streamURL={localStream.toURL()}
          style={styles.selfView}
          mirror
        />
      )}
      {remoteStream && (
        <RTCView
          streamURL={remoteStream.toURL()}
          style={styles.remoteView}
        />
      )}
      <Button title="Start Call" onPress={startCall} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'black' },
  selfView: {
    position: 'absolute', top: 10, right: 10, width: 100, height: 150, zIndex: 2,
  },
  remoteView: {
    flex: 1,
  },
});
