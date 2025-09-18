import React, { useContext, useEffect } from 'react';
import { WebSocketContext } from '../context/WebSocketContext';

const ChargerDashboard = () => {
  const { messages, isConnected } = useContext(WebSocketContext);

  // Log or alert new parsed message
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      try {
        const parsed = JSON.parse(lastMessage);
        console.log('Parsed WebSocket Message:', parsed); // ✅ Log to console
        alert(JSON.stringify(parsed)); // ✅ Or use alert if needed (uncomment to enable)
      } catch (err) {
        console.warn('Failed to parse message:', lastMessage);
      }
    }
  }, [messages]);

  const parsedMessages = messages.map(msg => {
    try {
      return JSON.parse(msg);
    } catch {
      return null;
    }
  }).filter(Boolean);

  const latestStatus = [...parsedMessages]
    .reverse()
    .find(msg => msg.event === 'status_update');

  const latestHeartbeat = [...parsedMessages]
    .reverse()
    .find(msg => Array.isArray(msg) && msg[2] === 'Heartbeat');

  return (
    <div className="card p-4 rounded-xl shadow-md bg-white text-gray-800">
      <h2 className="text-xl font-bold mb-4">Charger Dashboard</h2>

      <p><strong>WebSocket Status:</strong>
        <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
          {isConnected ? ' Connected' : ' Disconnected'}
        </span>
      </p>

      <p><strong>Status:</strong> {latestStatus?.status || 'Unknown'}</p>
      <p><strong>Activity:</strong> {latestStatus?.activity || 'Unknown'}</p>
      <p><strong>Connected:</strong> {latestStatus?.connectivity || 'Unknown'}</p>
      <p><strong>Last Heartbeat:</strong> {latestHeartbeat?.[3]?.currentTime || 'N/A'}</p>

        <div className="mt-4">
          <div className="overflow-y-auto max-h-60 bg-gray-100 rounded">
            <h3 className="font-semibold p-2 sticky top-0 bg-gray-100 z-10">
              Recent Messages:
            </h3>
            <ul className="text-sm space-y-1 px-2 pb-2">
              {messages.slice(-10).reverse().map((msg, idx) => (
                <li key={idx} className="mb-1">
                  <code className="break-words whitespace-pre-wrap block overflow-x-auto">
                    {JSON.stringify(msg)}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        </div>
    </div>
  );
};

export default ChargerDashboard;
