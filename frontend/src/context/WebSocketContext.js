// src/context/WebSocketContext.js
import React, { createContext, useEffect, useRef, useState } from 'react';

export const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {

  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);
  const WS_URL = "ws://localhost:9000/ws/charging/station/DTS-CC-001/CHG001/";
  const connectWebSocket = () => {
    socketRef.current = new WebSocket(WS_URL,"ocpp1.6");

    socketRef.current.onopen = () => {
      setIsConnected(true);
      alert("WebSocket connected.");
    };

    socketRef.current.onmessage = (event) => {
      console.log("Received:", event.data);
      setMessages((prev) => [...prev, event.data]);
    };

    socketRef.current.onclose = () => {
      setIsConnected(false);
      alert("WebSocket disconnected.");
    };

    socketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      alert("WebSocket error.");
    };
  };
  const sendMessage = (message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    } else {
      console.warn("🚫 WebSocket not connected. Cannot send message.");
    }
  };

  useEffect(() => {
    connectWebSocket();
  }, []);
  return (
    <WebSocketContext.Provider value={{ messages, sendMessage, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};
