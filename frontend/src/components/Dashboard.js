import React, { useEffect, useState } from 'react';
import axios from 'axios';

function Dashboard({ onSelectDoc }) {
  const [docs, setDocs] = useState([]);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [sort, setSort] = useState('created_at');
  const [loading, setLoading] = useState(false);

  const fetchDocs = async () => {
    try {
      setLoading(true);

      let url = `http://localhost:8000/api/documents?search=${search}&sort=${sort}`;
      if (status) {
        url += `&status=${status}`;
      }

      const res = await axios.get(url);
      setDocs(res.data.documents);

    } catch (err) {
      console.error("Error fetching docs:", err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch when filters change
  useEffect(() => {
    fetchDocs();
  }, [search, status, sort]);

  // Auto refresh every 2 sec
  useEffect(() => {
    const interval = setInterval(fetchDocs, 10000
        
    );
    return () => clearInterval(interval);
  }, [search, status, sort]);

  return (
    <div className="card">
      <h2>📄 Documents</h2>

      {/* 🔍 SEARCH + FILTER + SORT */}
      <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
        
        <input
          type="text"
          placeholder="Search filename..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Status</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>

        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="created_at">Sort by Time</option>
          <option value="filename">Sort by Name</option>
          <option value="status">Sort by Status</option>
        </select>

      </div>

      {/* ⏳ Loading */}
      {loading && <p>Loading...</p>}

      {/* 📊 TABLE */}
      <table>
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Progress</th>
          </tr>
        </thead>

        <tbody>
          {docs.length === 0 ? (
            <tr>
              <td colSpan="3">No documents found</td>
            </tr>
          ) : (
            docs.map((doc) => (
              <tr key={doc.id} onClick={() => onSelectDoc(doc.id)}>
                <td>{doc.filename}</td>

                <td>
                  <span className={`status-badge status-${doc.status}`}>
                    {doc.status}
                  </span>
                </td>

                <td>
                  <div className="progress-bar-container">
                    <div
                      className="progress-bar"
                      style={{ width: `${doc.progress}%` }}
                    />
                  </div>
                  <small>{doc.progress}%</small>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default Dashboard;