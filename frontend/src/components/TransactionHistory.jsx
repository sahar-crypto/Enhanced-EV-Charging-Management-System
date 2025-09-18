import React, { useContext } from 'react';
import { WebSocketContext } from '../context/WebSocketContext';

const TransactionHistory = () => {
  const { messages } = useContext(WebSocketContext);

  // Filter only StartTransaction and StopTransaction messages
  const transactions = messages.filter(
    (msg) =>
      Array.isArray(msg) &&
      msg.length >= 3 &&
      (msg[2] === "StartTransaction" || msg[2] === "StopTransaction")
  );

  return (
    <div className="card">
      <h2>Transaction History</h2>
      <ul>
        {transactions.map((txn, idx) => (
          <li key={idx}>
            <strong>{txn[2]}</strong> — {JSON.stringify(txn[3])}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TransactionHistory;
