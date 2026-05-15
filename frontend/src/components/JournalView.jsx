import React from 'react';
import { BookOpen } from 'lucide-react';

const JournalView = ({ entries }) => {
  return (
    <div className="panel">
      <div className="panel-header">
        <BookOpen size={20} />
        Vulnerability Journal (Attempts: {entries.length})
      </div>
      <div className="journal-container">
        {entries.map((entry, idx) => (
          <div key={idx} className={`journal-item ${entry.outcome === 'breached' ? 'breached' : ''}`}>
            <div className="journal-header">
              <span>Execution #{entry.attempt_number}</span>
              <span style={{ color: entry.outcome === 'breached' ? 'var(--danger)' : 'var(--text-muted)' }}>
                {entry.outcome.toUpperCase()}
              </span>
            </div>
            <div className="journal-payload">
              {entry.payload.length > 40 ? entry.payload.substring(0, 40) + '...' : entry.payload}
            </div>
            {entry.outcome === 'failed' && (
              <div className="journal-critique">
                {entry.gamma_critique}
              </div>
            )}
          </div>
        ))}
        {entries.length === 0 && (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', margin: 'auto', opacity: 0.5 }}>
            No vulnerability records.
          </div>
        )}
      </div>
    </div>
  );
};

export default JournalView;
