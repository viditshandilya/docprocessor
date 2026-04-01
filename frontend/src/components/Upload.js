import React, { useState } from 'react';
import axios from 'axios';

function Upload({ onDone }) {
  const [files, setFiles] = useState([]);

  const handleUpload = async () => {
    const formData = new FormData();
    for (let file of files) {
      formData.append('files', file);
    }

    await axios.post('http://localhost:8000/api/upload', formData);
    alert('Uploaded!');
    onDone();
  };

  return (
    <div className="card">
      <h2>Upload Files</h2>
      <input type="file" multiple onChange={(e) => setFiles(e.target.files)} />
      <br /><br />
      <button className="btn btn-primary" onClick={handleUpload}>
        Upload
      </button>
    </div>
  );
}

export default Upload;