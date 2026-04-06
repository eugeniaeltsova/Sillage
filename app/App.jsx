import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const ROTATING_PROMPTS = [
  "Every scent tells a story. What is yours?",
  "Describe a memory, a feeling, a person.",
  "I will find the fragrance.",
  "A rainy afternoon, a sun-warmed skin, a farewell.",
  "Everything has a scent. Even silence.",
  "What do you want the world to remember about you?",
];

function RotatingPrompt() {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);
  const [position, setPosition] = useState({ top: "30%", left: "40%" });

  useEffect(() => {
    const zones = [
      { top: [10, 25], left: [10, 40] },
      { top: [10, 25], left: [55, 80] },
      { top: [70, 85], left: [10, 40] },
      { top: [70, 85], left: [55, 80] },
      { top: [40, 60], left: [10, 25] },
      { top: [40, 60], left: [65, 80] },
    ];

    const timer = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex(i => (i + 1) % ROTATING_PROMPTS.length);
        const zone = zones[Math.floor(Math.random() * zones.length)];
        setPosition({
          top: `${zone.top[0] + Math.random() * (zone.top[1] - zone.top[0])}%`,
          left: `${zone.left[0] + Math.random() * (zone.left[1] - zone.left[0])}%`,
        });
        setVisible(true);
      }, 2000);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      className="rotating-prompt"
      style={{
        opacity: visible ? 0.5 : 0,
        position: 'absolute',
        top: position.top,
        left: position.left,
        transform: "translate(-50%, -50%)",
        transition: "opacity 2s ease-in-out",
        pointerEvents: "none",
        whiteSpace: "nowrap",
      }}
    >
      {ROTATING_PROMPTS[index]}
    </div>
  );
}

function NoteTag({ text, type }) {
  return <span className={`r-tag ${type === 'accord' ? 'accord' : ''}`}>{text}</span>;
}

function ResultCard({ result, index, isDarkHorse, description }) {
  const [visible, setVisible] = useState(false);
  const [showStory, setShowStory] = useState(false);
  const p = result.payload;

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), index * 120);
    return () => clearTimeout(timer);
  }, [index]);

  const notes = p.Top ? p.Top.split(',').slice(0, 3) : [];
  const accords = p.accords ? p.accords.split(',').slice(0, 3) : [];

  return (
    <div className={`result-card ${isDarkHorse ? 'dark-horse' : ''} ${visible ? 'visible' : ''}`}>
      <div className="card-main">
        {isDarkHorse
          ? <div className="dh-label">Hidden gem</div>
          : <div className="r-num">{String(index + 1).padStart(2, '0')}</div>
        }
        <div className="r-name">{p.Perfume}</div>
        <div className="r-brand">
          {p.Brand}
          {p.Perfumer1 && p.Perfumer1 !== 'unknown' && ` · ${p.Perfumer1}`}
        </div>
        <div className="r-tags">
          {notes.map(n => <NoteTag key={n} text={n.trim()} type="note" />)}
          {accords.map(a => <NoteTag key={a} text={a.trim()} type="accord" />)}
        </div>
        {showStory && description && (
          <div className="card-story">{description}</div>
        )}
        <div className="card-footer">
          {p.Gender && <span className="r-gender">{p.Gender}</span>}
          <button className="r-voice" onClick={() => setShowStory(s => !s)}>
            <span className="r-voice-icon">{showStory ? '−' : '▶'}</span>
            {showStory ? 'Close' : 'Read the story'}
          </button>
        </div>
      </div>
      <div className="r-meta">
        {p.Year > 0 && <div className="r-year">{p.Year}</div>}
        {p['Rating Value'] && (
          <div className="r-rating">{Number(p['Rating Value']).toFixed(2)} / 5</div>
        )}
        {p.url && (
          <a className="r-link" href={p.url} target="_blank" rel="noreferrer">View ↗</a>
        )}
      </div>
    </div>
  );
}

function Message({ msg }) {
  // Plain assistant or user message
  if (msg.role === 'assistant' || msg.role === 'user') {
    return (
      <div className={`msg ${msg.role}`}>
        <div className="msg-label">{msg.role === 'assistant' ? 'Sillage' : 'You'}</div>
        <div className="msg-bubble">{msg.content}</div>
      </div>
    );
  }

  // Results block — always renders fully, stories always available
  if (msg.role === 'results') {
    const { intro, descriptions = [], results, hasDarkHorse } = msg;

    return (
      <div className="results-block">
        {intro && (
          <div className="msg assistant">
            <div className="msg-label">Sillage</div>
            <div className="msg-bubble">{intro}</div>
          </div>
        )}

        {results.length === 0 && (
          <div className="msg-bubble">{msg.reply}</div>
        )}

        {results.map((r, i) => (
          <ResultCard
            key={r.id}
            result={r}
            index={i}
            isDarkHorse={i === results.length - 1 && hasDarkHorse}
            description={descriptions[i] || ''}
          />
        ))}

        <div className="results-followup">
          Tell me what you think — or shall I refine the selection?
        </div>
      </div>
    );
  }

  return null;
}

function TypingIndicator() {
  return (
    <div className="msg assistant">
      <div className="msg-label">Sillage</div>
      <div className="msg-bubble typing">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [apiMessages, setApiMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll only for non-results messages
  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.role === 'results') return;
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    if (!text.trim() || loading) return;
    setStarted(true);
    setInput('');

    const newApiMessages = [...apiMessages, { role: 'user', content: text }];
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setApiMessages(newApiMessages);
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/chat', {
        messages: newApiMessages
      });

      const { reply, messages: updatedMessages } = res.data;

      // Find result data from last tool message
      let resultData = null;
      for (let i = updatedMessages.length - 1; i >= 0; i--) {
        const m = updatedMessages[i];
        if (m.role === 'tool' && m.content && m.content !== 'null') {
          try {
            const parsed = JSON.parse(m.content);
            if (parsed.results) {
              resultData = parsed;
              break;
            }
          } catch {}
        }
      }

      setApiMessages(updatedMessages);

      if (resultData) {
        const raw = reply || '';
        const paragraphs = raw.split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);
        const intro = paragraphs.length > 1 ? paragraphs[0] : raw;
        const descriptions = paragraphs.length > 1 ? paragraphs.slice(1) : [];

        setMessages(prev => [...prev, {
          role: 'results',
          results: resultData.results,
          hasDarkHorse: resultData.dark_horse,
          reply,
          intro,
          descriptions,
        }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went quiet on my end. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setApiMessages([]);
    setStarted(false);
    setInput('');
  };

  return (
    <div className="app">
      <header className="header" style={{ position: 'relative', zIndex: 1 }}>
        <div className="logo">Sillage</div>
        <div className="tagline">Fragrance Discovery</div>
        <button className="new-thread-btn" onClick={handleNewChat}>
          New Chat
        </button>
      </header>

      <div className="chat-area" style={{ position: 'relative', zIndex: 1 }}>
        {/* Rotating prompts float inside chat-area on initial screen, scroll away naturally */}
        {!started && <RotatingPrompt />}

        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="input-area" style={{ position: 'relative', zIndex: 1 }}>
        <input
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Describe a scent, a memory, a feeling..."
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => send(input)}
          disabled={loading}
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
