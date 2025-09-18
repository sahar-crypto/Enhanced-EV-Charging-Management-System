import { CommandSocketContext } from '../context/CommandingWebSocketContext';
import { useContext } from 'react';

const ChargingControls = () => {
  const { sendCommand } = useContext(CommandSocketContext);

  const generateUniqueId = () => `msg-${Date.now()}`;

  const handleStart = () => {
    const uniqueId = generateUniqueId();
    sendCommand([
      2,
      uniqueId,
      "RemoteStartTransaction",
      {
        connectorId: 1,
        idTag: "TEST_TAG"
      }
    ]);
    alert("Sent start command.");
    console.log("Sent start command.");
  };

  const handleStop = () => {
    const uniqueId = generateUniqueId();
    sendCommand([
      2,
      uniqueId,
      "RemoteStopTransaction",
      {
        transactionId: 1
      }
    ]);
    alert("Sent stop command.");
    console.log("Sent stop command");
  };

  return (
    <div className="card">
      <h2>Charging Controls</h2>
      <button onClick={handleStart}>Start Charging</button>
      <button onClick={handleStop}>Stop Charging</button>
    </div>
  );
};

export default ChargingControls;
