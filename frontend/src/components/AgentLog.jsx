import React from 'react';
import { Activity } from 'lucide-react';

const AgentLog = ({ messages }) => {
  return (
    <div className="panel" style={{ overflow: 'hidden' }}>
      <div className="panel-header">
        <Activity size={20} />
        Live Assessment Feed
      </div>
      <div className="feed-container" id="feed-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`feed-item ${msg.level}`}>
            <div className="feed-header">
              <span className="feed-agent">{msg.agent.toUpperCase()}</span>
              <span className="feed-time">{msg.timestamp}</span>
            </div>
            <div className="feed-message">{msg.message}</div>
          </div>
        ))}
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', margin: 'auto', opacity: 0.5 }}>
            Feed will populate when scan initiates.
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentLog;
