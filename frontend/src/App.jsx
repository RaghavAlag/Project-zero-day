import React, { useState, useEffect, useRef } from 'react';
import AttackPanel from './components/AttackPanel';
import AgentLog from './components/AgentLog';
import JournalView from './components/JournalView';
import BreachAlert from './components/BreachAlert';
import DiffViewer from './components/DiffViewer';
import './styles/main.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [journal, setJournal] = useState([]);
  const [scanStatus, setScanStatus] = useState('idle');
  const [showBreach, setShowBreach] = useState(false);
  const [diffData, setDiffData] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
      
      // Auto-scroll logic happens in AgentLog (we'll let CSS handle some, or add a ref there later)
      const feedContainer = document.getElementById('feed-container');
      if (feedContainer) {
        setTimeout(() => {
          feedContainer.scrollTop = feedContainer.scrollHeight;
        }, 50);
      }

      if (data.level === 'breach') {
        setShowBreach(true);
        setScanStatus('breached');
        setTimeout(() => setShowBreach(false), 3500);
      } else if (data.level === 'diff') {
        setDiffData(data.extra);
      } else if (data.message === "Red Swarm exhausted all attempts. Target hardened or scope exceeded.") {
        setScanStatus('failed');
      }
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Poll journal while scanning
  useEffect(() => {
    let interval;
    if (scanStatus === 'running') {
      interval = setInterval(async () => {
        try {
          const res = await fetch('http://localhost:8000/journal');
          const data = await res.json();
          setJournal(data);
        } catch (e) {
          console.error("Failed to fetch journal", e);
        }
      }, 3000);
    } else if (scanStatus !== 'idle') {
      // Fetch one last time when done
      fetch('http://localhost:8000/journal')
        .then(res => res.json())
        .then(data => setJournal(data))
        .catch(e => console.error(e));
    }
    
    return () => clearInterval(interval);
  }, [scanStatus]);

  const handleLaunch = async (url, vulnType) => {
    setScanStatus('running');
    setMessages([]);
    setJournal([]);
    
    try {
      await fetch('http://localhost:8000/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: url, vuln_type: vulnType })
      });
    } catch (e) {
      console.error("Launch failed", e);
      setScanStatus('failed');
    }
  };

  return (
    <>
      <BreachAlert show={showBreach} />
      <DiffViewer diffData={diffData} onClose={() => setDiffData(null)} />
      <div className="dashboard">
        <AttackPanel onLaunch={handleLaunch} scanStatus={scanStatus} />
        <AgentLog messages={messages} />
        <JournalView entries={journal} />
      </div>
    </>
  );
}

export default App;
