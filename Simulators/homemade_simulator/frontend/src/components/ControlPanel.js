import React, { useState, useRef } from "react";

function ControlPanel() {
  const [isConnected, setIsConnected] = useState(false);
  const [isPluggedIn, setIsPluggedIn] = useState(false);
  const [isCharging, setIsCharging] = useState(false);
  const [messages, setMessages] = useState([]); // ⬅️ State to hold server responses
  const socketRef = useRef(null);

  const WS_URL = "ws://localhost:9000/ws/charging/station/DTS-CC-001/CHG001/";

  const connectWebSocket = () => {
    socketRef.current = new WebSocket(WS_URL);

    socketRef.current.onopen = () => {
      setIsConnected(true);
      alert("WebSocket connected.");
    };

    socketRef.current.onmessage = (event) => {
      console.log("Received:", event.data);
      setMessages((prev) => [...prev, event.data]); // ⬅️ Append message to state
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

  const disconnectWebSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
    }
  };

  const handleToggleConnection = () => {
    if (!isConnected) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
  };

  const sendStatus = (status) => {
    if (socketRef.current && isConnected) {
      const msg = [
        2,
        crypto.randomUUID(),
        "StatusNotification",
        {
          connectorId: 1,
          status: status,
          timestamp: new Date().toISOString(),
        },
      ];
      socketRef.current.send(JSON.stringify(msg));
      console.log(`Sent status: ${status}`);
    } else {
      alert("WebSocket is not connected.");
    }
  };

  const togglePlug = () => {
    if (!isConnected) {
      alert("Connect first!");
      return;
    }
    const newStatus = !isPluggedIn;
    setIsPluggedIn(newStatus);
    sendStatus(newStatus ? "PluggedIn" : "Unplugged");
  };

  const toggleCharging = () => {
    if (!isConnected) {
      alert("Connect first!");
      return;
    }
    const newStatus = !isCharging;
    setIsCharging(newStatus);
    sendStatus(newStatus ? "Charging" : "Stopped");
  };

  return (
    <div className="control-panel">
      <h2>Control Panel</h2>

      <button
        onClick={handleToggleConnection}
        className={isConnected ? "green-btn" : "gray-btn"}
      >
        {isConnected ? "Disconnect" : "Connect"}
      </button>

      <br /><br />

      <button
        onClick={togglePlug}
        className={isPluggedIn ? "blue-btn" : "red-btn"}
        disabled={!isConnected}  // ⬅️ disable if not connected
      >
        {isPluggedIn ? "Unplug" : "Plug In"}
      </button>

      <button
        onClick={toggleCharging}
        className={isCharging ? "green-btn" : "gray-btn"}
        disabled={!isConnected}  // ⬅️ disable if not connected
      >
        {isCharging ? "Stop Charging" : "Start Charging"}
      </button>

      <br /><br />

      <div className="message-log">
        <h3>Server Responses</h3>
        <ul>
          {messages.map((msg, idx) => (
            <li key={idx}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default ControlPanel;
