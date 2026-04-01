import React, { useEffect, useState } from 'react';
import axios from 'axios';

function DocumentDetail({ docId, onBack }) {
  const [doc, setDoc] = useState(null);

  const fetchDoc = async () => {
    const res = await axios.get(`http://localhost:8000/api/documents/${docId}`);
    setDoc(res.data);
  };

  useEffect(() => {
    fetchDoc();
    const interval = setInterval(fetchDoc, 2000);
    return () => clearInterval(interval);
  }, [docId]);

  const exportJSON = () => {
    window.open(`http://localhost:8000/api/documents/${docId}/export/json`);
  };

  const exportCSV = () => {
    window.open(`http://localhost:8000/api/documents/${docId}/export/csv`);
  };

  if (!doc) return <div>Loading...</div>;

  return (
    <div className="card">
      <button onClick={onBack} className="btn btn-secondary">Back</button>

      <h2>{doc.filename}</h2>
      <p>Status: {doc.status}</p>

      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${doc.progress}%` }} />
      </div>

      {doc.result && (
        <>
          <h3>Result</h3>
          <pre>{JSON.stringify(doc.result, null, 2)}</pre>

          <button className="btn btn-success" onClick={exportJSON}>
            Export JSON
          </button>
          <button className="btn btn-primary" onClick={exportCSV}>
            Export CSV
          </button>
        </>
      )}
    </div>
  );
}

export default DocumentDetail;