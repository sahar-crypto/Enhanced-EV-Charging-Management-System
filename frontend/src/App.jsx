import React from 'react';
import { WebSocketProvider } from './context/WebSocketContext';
import { CommandSocketProvider } from "./context/CommandingWebSocketContext";
import ChargerDashboard from './components/ChargerDashboard';
import ChargingControls from './components/ChargingControls';
import TransactionHistory from './components/TransactionHistory';
import './App.css';

const App = () => {
  return (
    <WebSocketProvider>
        <CommandSocketProvider>
          <div className="container">
            <h1>EV Charging System</h1>
            <ChargerDashboard />
            <ChargingControls />
            <TransactionHistory />
          </div>
        </CommandSocketProvider>
    </WebSocketProvider>
  );
};

export default App;
