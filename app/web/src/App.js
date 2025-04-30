import React, { useState } from 'react';
import logo from './logo.svg'; // Corrected import path
import './App.css';

function App() {
  const [apiKey, setApiKey] = useState('');
  const [endpoint, setEndpoint] = useState('summary'); // Default endpoint
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleApiKeyChange = (event) => {
    setApiKey(event.target.value);
  };

  const handleEndpointChange = (event) => {
    setEndpoint(event.target.value);
    // Clear file and url when endpoint changes
    setFile(null);
    setUrl('');
    setResponse(null); // Clear previous response
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setUrl(''); // Clear URL if file is selected
    setResponse(null); // Clear previous response
  };

  const handleUrlChange = (event) => {
    setUrl(event.target.value);
    setFile(null); // Clear file if URL is entered
    setResponse(null); // Clear previous response
  };

  const handleSubmit = async () => {
    if (!apiKey) {
      alert('Please enter your API Key.');
      return;
    }

    if (endpoint !== 'health' && !file && !url) { // Health endpoint doesn't need file/url
      alert('Please upload a file or enter a URL for non-health endpoints.');
      return;
    }

    setLoading(true);
    setResponse(null);

    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    } else if (url) {
      formData.append('url', url);
    }

    // Construct the full URL with API key and selected endpoint
    // Assuming Tiko is running on http://localhost:9999
    const finalUrl = `http://localhost:9999/${endpoint}?token=${apiKey}`;

    try {
      // Using POST for all for simplicity, verify Tiko supports POST for health
      const res = await fetch(finalUrl, {
        method: 'POST',
        body: endpoint !== 'health' ? formData : null, // Only send body for non-health endpoints
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP error! status: ${res.status}, message: ${errorText}`);
      }

      const data = await res.text(); // Tiko returns plain text for summary/extract, maybe JSON for /json
      setResponse(data); // Display raw response for now
    } catch (error) {
      console.error('Error calling Tiko API:', error);
      setResponse(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Render additional parameters based on selected endpoint
  const renderAdditionalParams = () => {
    switch (endpoint) {
      case 'summary':
        return (
          <div style={{ margin: '10px 0' }}>
             {/* Add state and handlers for model and api_key overrides later */}
             <label htmlFor="summary-model">Model Override (Optional):</label>
             <input type="text" id="summary-model" placeholder="e.g., gpt-4" style={{ marginLeft: '5px' }} />
             {/* <label htmlFor="summary-apikey">API Key Override (Optional):</label>
             <input type="text" id="summary-apikey" placeholder="Override API Key" /> */}
          </div>
        );
      case 'json':
        return (
          <div style={{ margin: '10px 0' }}>
             {/* Add state and handler for jsonType later */}
             <label htmlFor="json-type">JSON Type (Optional):</label>
             <input
                type="text"
                id="json-type"
                placeholder="e.g., contrato, decisao"
                style={{ marginLeft: '5px' }}
             />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="App">
      {/* Conditionally render based on API key */}
      {apiKey ? (
        // Main application interface will go here later
        <div className="App-main-interface"> {/* Changed from <header> to <div> */}
          <h1>Tiko Document Processor</h1>
          <div>
            <label htmlFor="endpoint-select" style={{ marginRight: '10px' }}>Choose Endpoint:</label>
            <select id="endpoint-select" value={endpoint} onChange={handleEndpointChange}>
              <option value="summary">/summary</option>
              <option value="extract">/extract</option>
              <option value="json">/json</option>
              <option value="health">/health</option>
            </select>
          </div>

          {endpoint !== 'health' && (
            <div style={{ margin: '20px 0' }}>
              <p>Upload a file or provide a URL:</p>
              <input
                type="file"
                onChange={handleFileChange}
                disabled={!!url} // Disable if URL is entered
              />
              <p>- OR -</p>
              <input
                type="text"
                placeholder="Enter URL"
                value={url}
                onChange={handleUrlChange}
                disabled={!!file} // Disable if file is selected
                style={{ padding: '5px', fontSize: '1em' }}
              />
            </div>
          )}

          {renderAdditionalParams() /* Render additional parameters based on endpoint */}

          <button onClick={handleSubmit} disabled={loading || (endpoint !== 'health' && !file && !url)}>
            {loading ? 'Processing...' : 'Send Request'}
          </button>

          {response && (
            <div className="response-area" style={{ marginTop: '20px', textAlign: 'left', border: '1px solid #ccc', padding: '10px', backgroundColor: '#f9f9f9' }}>
              <h3>Response:</h3>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{response}</pre>
            </div>
          )}

        </div>
      ) : (
        // API Key input screen
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1>Enter Tiko API Key</h1>
          <input
            type="text"
            placeholder="Enter API Key"
            value={apiKey}
            onChange={handleApiKeyChange}
            style={{ padding: '10px', margin: '20px', fontSize: '1em' }}
          />
        </header>
      )}
    </div>
  );
}

export default App;
