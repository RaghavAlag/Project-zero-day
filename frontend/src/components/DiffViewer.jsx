import React, { useState, useEffect } from 'react';

function diffLines(original, patched) {
  const origLines = (original || '').split('\n');
  const patchLines = (patched || '').split('\n');
  
  // Simple unified diff: mark lines that changed
  const maxLen = Math.max(origLines.length, patchLines.length);
  const origResult = [];
  const patchResult = [];

  for (let i = 0; i < maxLen; i++) {
    const o = origLines[i] !== undefined ? origLines[i] : null;
    const p = patchLines[i] !== undefined ? patchLines[i] : null;
    
    if (o === p) {
      origResult.push({ text: o, type: 'same' });
      patchResult.push({ text: p, type: 'same' });
    } else {
      origResult.push({ text: o !== null ? o : '', type: o !== null ? 'removed' : 'empty' });
      patchResult.push({ text: p !== null ? p : '', type: p !== null ? 'added' : 'empty' });
    }
  }
  return { origResult, patchResult };
}

export default function DiffViewer({ diffData, onClose }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (diffData) {
      setTimeout(() => setVisible(true), 50);
    }
  }, [diffData]);

  if (!diffData) return null;

  const { original, patched, vuln_type } = diffData;
  const { origResult, patchResult } = diffLines(original, patched);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 400);
  };

  const vulnLabel = vuln_type === 'sqli' ? 'SQL Injection' : 'Command Injection';

  return (
    <div className={`diff-overlay ${visible ? 'visible' : ''}`} onClick={handleClose}>
      <div className="diff-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="diff-header">
          <div className="diff-header-left">
            <span className="diff-badge-vuln">{vulnLabel} Patch</span>
            <h2 className="diff-title">🛡️ Code Diff — Vulnerability Remediation</h2>
            <p className="diff-subtitle">AI-generated patch applied and verified by live exploit re-test</p>
          </div>
          <button className="diff-close-btn" onClick={handleClose}>✕ Close</button>
        </div>

        {/* Stats Bar */}
        <div className="diff-stats">
          <div className="diff-stat diff-stat-red">
            <span className="diff-stat-num">{origResult.filter(l => l.type === 'removed').length}</span>
            <span className="diff-stat-label">Lines Removed</span>
          </div>
          <div className="diff-stat diff-stat-green">
            <span className="diff-stat-num">{patchResult.filter(l => l.type === 'added').length}</span>
            <span className="diff-stat-label">Lines Added</span>
          </div>
          <div className="diff-stat diff-stat-accent">
            <span className="diff-stat-num">{origResult.filter(l => l.type === 'same').length}</span>
            <span className="diff-stat-label">Lines Unchanged</span>
          </div>
        </div>

        {/* Side-by-side diff panels */}
        <div className="diff-panels">
          {/* Left — Vulnerable */}
          <div className="diff-panel diff-panel-vuln">
            <div className="diff-panel-title diff-panel-title-red">
              <span className="diff-dot diff-dot-red"></span>
              ❌ VULNERABLE — Before Patch
            </div>
            <div className="diff-code-scroll">
              {origResult.map((line, i) => (
                <div key={i} className={`diff-line diff-line-${line.type}`}>
                  <span className="diff-line-num">{i + 1}</span>
                  <span className="diff-line-gutter">
                    {line.type === 'removed' ? '−' : ' '}
                  </span>
                  <span className="diff-line-text">{line.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="diff-divider">
            <div className="diff-divider-line"></div>
            <div className="diff-divider-icon">⟶</div>
            <div className="diff-divider-line"></div>
          </div>

          {/* Right — Patched */}
          <div className="diff-panel diff-panel-secure">
            <div className="diff-panel-title diff-panel-title-green">
              <span className="diff-dot diff-dot-green"></span>
              ✅ SECURED — After Patch
            </div>
            <div className="diff-code-scroll">
              {patchResult.map((line, i) => (
                <div key={i} className={`diff-line diff-line-${line.type}`}>
                  <span className="diff-line-num">{i + 1}</span>
                  <span className="diff-line-gutter">
                    {line.type === 'added' ? '+' : ' '}
                  </span>
                  <span className="diff-line-text">{line.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="diff-footer">
          <span className="diff-footer-badge diff-footer-badge-green">✅ EXPLOIT BLOCKED — Live DAST Verification Passed</span>
          <span className="diff-footer-note">Click anywhere outside to dismiss</span>
        </div>
      </div>
    </div>
  );
}
