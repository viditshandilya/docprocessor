import React, { useState } from 'react';
import Upload from './components/Upload';
import Dashboard from './components/Dashboard';
import DocumentDetail from './components/DocumentDetail';
import './App.css';

function App() {
  const [page, setPage] = useState('dashboard');
  const [selectedDocId, setSelectedDocId] = useState(null);

  const goToDetail = (id) => {
    setSelectedDocId(id);
    setPage('detail');
  };

  const goToDashboard = () => {
    setSelectedDocId(null);
    setPage('dashboard');
  };

  const goToUpload = () => {
    setPage('upload');
  };

  return (
    <div className="app">
      <nav className="navbar">
        <h1 onClick={goToDashboard} style={{cursor:'pointer'}}>📄 DocProcessor</h1>
        <div>
          <button onClick={goToDashboard} className="nav-btn">Dashboard</button>
          <button onClick={goToUpload} className="nav-btn">Upload</button>
        </div>
      </nav>

      <div className="content">
        {page === 'dashboard' && <Dashboard onSelectDoc={goToDetail} />}
        {page === 'upload' && <Upload onDone={goToDashboard} />}
        {page === 'detail' && <DocumentDetail docId={selectedDocId} onBack={goToDashboard} />}
      </div>
    </div>
  );
}

export default App;