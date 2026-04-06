function Message({ msg }) {
  if (msg.role === 'results') {
    // Split reply into per-perfume descriptions
    const raw = msg.reply || '';

// Split by empty lines (paragraphs)
const paragraphs = raw
  .split(/\n\s*\n/)   // split on blank lines
  .map(p => p.trim())
  .filter(Boolean);

let intro = '';
let descriptions = [];

if (paragraphs.length > 1) {
  intro = paragraphs[0];
  descriptions = paragraphs.slice(1);
} else {
  // fallback: no structure
  intro = raw;
}

    console.log('descriptions:', descriptions);
    console.log('reply:', msg.reply);
    console.log('Rendering results...');
console.log('Number of results:', msg.results.length);
console.log('Results:', msg.results.map(r => r.payload.Perfume));
console.log('Number of descriptions:', descriptions.length);
console.log('Descriptions:', descriptions);
    
    
    /*return (
      <div className="results-block">
        {msg.results.map((r, i) => (
          <ResultCard
            key={r.id}
            result={r}
            index={i}
            isDarkHorse={i === msg.results.length - 1 && msg.hasDarkHorse}
            description={descriptions[i] || ''}
          />
        ))}
        <div className="results-followup">
          Tell me what you think — or shall I refine the selection?
        </div>
      </div>
    );*/

      return (
    <div className="results-block">

      {intro && (
    <div className="msg assistant">
    <div className="msg-label">Sillage</div>
    <div className="msg-bubble">{intro}</div>
   </div>
    )}

  

      {/*  SHOW TEXT IF NO RESULTS */}
      {msg.results.length === 0 && (
        <div className="msg-bubble">{msg.reply}</div>
      )}

      {/* NORMAL RESULTS */}
      {msg.results.length > 0 && msg.results.map((r, i) => (
        <ResultCard
          key={r.id}
          result={r}
          index={i}
          isDarkHorse={i === msg.results.length - 1 && msg.hasDarkHorse}
          description={descriptions[i] || ''}
        />
      ))}

      <div className="results-followup">
        Tell me what you think — or shall I refine the selection?
      </div>
    </div>
  );
  }

  return (
    <div className={`msg ${msg.role}`}>
      <div className="msg-label">{msg.role === 'assistant' ? 'Sillage' : 'You'}</div>
      <div className="msg-bubble">{msg.content}</div>
    </div>
  );
}


  /*{!started && (
        <div className="welcome" style={{ position: 'relative', zIndex: 1, height: '70vh' }}>
          <RotatingPrompt />
          
        </div>
      )}*/