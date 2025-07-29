// phone/FrontEnd/constants/wsRoutes.js
import { WS_URL } from '../config';


// VideoCallTestScreen
export const getVideoCallRoomURL = (roomName) => `${WS_URL}/ws/mobile/video-call/${roomName}/`;
