import React, { useState } from 'react';
import { Target, Zap, ArrowRight, Shield } from 'lucide-react';

const AttackPanel = ({ onLaunch, scanStatus }) => {
  const [url, setUrl] = useState('http://localhost:5000');
  const [vulnType, setVulnType] = useState('sqli');

  const handleLaunch = () => {
    onLaunch(url, vulnType);
  };

  return (
    <div className="panel">
      <div className="hero-section">
        <h1 className="hero-title">
          Try and test.<br />
          <span className="highlight">Often.</span>
        </h1>
        <p className="hero-subtitle">
          This is a digital playground for personal experiments.<br/>
          Select a target to begin the autonomous assessment.
        </p>
      </div>
      
      <div className="panel-header" style={{ marginTop: 'auto' }}>
        <Target size={20} />
        Mission Control
      </div>

      <div className="input-group">
        <label>Target URL</label>
        <input 
          type="text" 
          className="input-field" 
          value={url} 
          onChange={e => setUrl(e.target.value)}
        />
      </div>

      <div className="input-group">
        <label>Vulnerability Class</label>
        <select 
          className="input-field" 
          value={vulnType} 
          onChange={e => setVulnType(e.target.value)}
        >
          <option value="sqli">SQL Injection</option>
          <option value="cmdi">Command Injection</option>
        </select>
      </div>

      <button 
        className={`btn ${scanStatus === 'running' ? 'running' : ''}`}
        onClick={handleLaunch}
        disabled={scanStatus === 'running'}
      >
        <Zap size={20} />
        {scanStatus === 'running' ? 'Scanning Network...' : 'Search Vulnerabilities'}
        <ArrowRight size={20} style={{ marginLeft: 'auto' }} />
      </button>

      <div className={`status-badge ${scanStatus}`}>
        {scanStatus === 'idle' && 'System Idle - Awaiting Target'}
        {scanStatus === 'running' && 'Assessment in Progress'}
        {scanStatus === 'breached' && 'Vulnerability Confirmed'}
        {scanStatus === 'failed' && 'Assessment Complete - No Vectors Found'}
      </div>
    </div>
  );
};

export default AttackPanel;
