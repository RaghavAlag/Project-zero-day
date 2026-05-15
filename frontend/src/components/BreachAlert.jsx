import React from 'react';
import { ShieldAlert } from 'lucide-react';

const BreachAlert = ({ show, onClose }) => {
  if (!show) return null;

  return (
    <div className="breach-overlay" onClick={onClose}>
      <div className="breach-card">
        <ShieldAlert className="breach-icon" />
        <div className="breach-title">SYSTEM BREACHED</div>
        <div className="breach-subtitle">CRITICAL VULNERABILITY EXPLOITED</div>
      </div>
    </div>
  );
};

export default BreachAlert;
