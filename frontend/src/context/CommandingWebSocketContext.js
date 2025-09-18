import React, {createContext, useEffect, useRef, useState} from 'react';

export const CommandSocketContext = createContext();

export const CommandSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const WS_URL = "ws://localhost:9000/ws/charging/station/DTS-CC-001/CHG001/charge/";
  const connectWebSocket = () => {
    socketRef.current = new WebSocket(WS_URL);

    socketRef.current.onopen = () => {
      setIsConnected(true);
      console.log("⚡ Command WebSocket connected");
      alert("WebSocket connected.");
    };

    socketRef.current.onclose = () => {
      setIsConnected(false);
      console.log("🛑 Command WebSocket disconnected");
    };
  };

  const sendCommand = (message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    } else {
      console.warn("❗ Command socket not connected.");
    }
  };

  useEffect(() => {
    connectWebSocket();
  }, []);

  return (
    <CommandSocketContext.Provider value={{ sendCommand }}>
      {children}
    </CommandSocketContext.Provider>
  );
};
