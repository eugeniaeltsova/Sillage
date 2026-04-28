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

const STARTER_CHIPS = [
  "Something woody and dark for evenings",
  "Fresh and marine, unisex",
  "Warm oriental, like a summer embrace",
  "Something unexpected — surprise me",
  "Powerful and musky",
  "Light and floral, perfect for spring",
];

function RotatingPrompt() {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);
  const [position, setPosition] = useState({ top: "50%", left: "50%" });

  useEffect(() => {
    const timer = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex(i => (i + 1) % ROTATING_PROMPTS.length);
        setPosition({
          top: `${20 + Math.random() * 60}%`,
          left: `${35 + Math.random() * 30}%`,
        });
        setVisible(true);
      }, 2000);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rotating-prompt" style={{
      opacity: visible ? 0.5 : 0,
      position: 'absolute',
      top: position.top,
      left: position.left,
      transform: "translate(-50%, -50%)",
      transition: "opacity 2s ease-in-out",
      pointerEvents: "none",
    }}>
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

// Result blocks are always rendered — never hidden.
// Each block is self-contained with its own frozen descriptions.
function ResultBlock({ msg }) {
  const { intro, descriptions = [], results, hasDarkHorse, searchId } = msg;

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
          key={`${searchId}-${r.id}`}
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

function Message({ msg }) {
  if (msg.role === 'results') {
    return <ResultBlock msg={msg} />;
  }

  return (
    <div className={`msg ${msg.role}`}>
      <div className="msg-label">{msg.role === 'assistant' ? 'Sillage' : 'You'}</div>
      <div className="msg-bubble">{msg.content}</div>
    </div>
  );
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
  // Ref to the scrollable chat div itself
  const chatAreaRef = useRef(null);
  // Sentinel div at the very bottom — used to scroll text messages into view
  const bottomRef = useRef(null);

  useEffect(() => {
    const lastMsg = messages[messages.length - 1];

    if (lastMsg?.role === 'results') {
      // Scroll the top of the result block into view so intro + first card are visible
      const el = chatAreaRef.current;
      if (!el) return;
      const blocks = el.querySelectorAll('.results-block');
      const last = blocks[blocks.length - 1];
      if (last) {
        last.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      return;
    }

    // For user/assistant text messages and the typing indicator:
    // defer one frame so the DOM has painted before we measure scroll height
    const id = setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
    return () => clearTimeout(id);
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
      const res = await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/chat`, {
        messages: newApiMessages
      });

      const { reply, messages: updatedMessages } = res.data;

      // Find the last tool message that contains search results
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

        // Freeze descriptions at arrival time — match by perfume name, fall back to position
        const descriptions = resultData.results.map((r, i) => {
          const name = r.payload?.Perfume || '';
          const matched = paragraphs.find(p =>
            name && p.toLowerCase().includes(name.toLowerCase())
          );
          return matched || paragraphs[i + 1] || '';
        });

        const cardParagraphs = new Set(descriptions.filter(Boolean));
        const intro = paragraphs.find(p => !cardParagraphs.has(p)) || paragraphs[0] || raw;

        setMessages(prev => [...prev, {
          role: 'results',
          searchId: Date.now(),
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

  return (
    <div className="app">
      <header className="header" style={{ position: 'relative', zIndex: 1 }}>
        <div className="logo">Sillage</div>
        <div className="tagline">Fragrance Discovery</div>
        <button className="new-thread-btn" onClick={() => {
          setMessages([]);
          setApiMessages([]);
          setStarted(false);
          setInput('');
        }}>
          New Chat
        </button>
      </header>

      {/* ref is now on the scrollable div itself */}
      <div className="chat-area" ref={chatAreaRef} style={{ position: 'relative', zIndex: 1 }}>
        {!started && <RotatingPrompt />}
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {!started && (
        <div className="starter-chips">
          {STARTER_CHIPS.map(chip => (
            <button key={chip} className="starter-chip" onClick={() => send(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}

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