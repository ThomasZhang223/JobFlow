'use client';
import { useState } from 'react';

export default function Home() {
  const [textbox1, setTextbox1] = useState('');
  const [textbox2, setTextbox2] = useState('');
  const [jsonString, setJsonString] = useState('');
  const [status, setStatus] = useState<'idle'|'sending'|'sent'|'error'>('idle');
  const [responseText, setResponseText] = useState('');

  const handleSubmit = async () => {
    const text1 = textbox1;
    const json = JSON.stringify(text1);
    setJsonString(json);
    setStatus('sending');
    setResponseText('');

    try {
      const res = await fetch('http://localhost:8000/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json,
      });

      
      if (!res.ok) {
        const errMsg = await res.json();
        console.log('Server error response:', errMsg);
      }

      // Try to parse JSON response if present
      let data = await res.json(); 

      setStatus('sent');
      setResponseText(data);
      console.log('Server response:', data);
    } catch (err: any) {
      setStatus('error');
      setResponseText(err?.message || String(err));
      console.error('Submit error', err);
    }
  };

  return (
    <section>
      <textarea
        className="border"
        value={textbox1}
        onChange={(e) => setTextbox1((e.target as HTMLTextAreaElement).value)}
        placeholder="Enter first value"
      />

      <button className="border" onClick={handleSubmit} disabled={status === 'sending'}>
        {status === 'sending' ? 'Sending...' : 'Submit'}
      </button>

      {jsonString && (
        <div className="mt-2">
          <strong>Request body:</strong>
          <pre className="mt-1 p-2 border bg-gray-100">{jsonString}</pre>
        </div>
      )}

      {status !== 'idle' && (
        <div className="mt-2">
          <strong>Status:</strong> {status}
          <div className="mt-1">
            <strong>Response:</strong>
            <pre className="mt-1 p-2 border bg-gray-50">{responseText}</pre>
          </div>
        </div>
      )}
    </section>
  );
}
