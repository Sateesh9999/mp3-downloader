import { useState } from 'react'
import './App.css'

const backendUrl = 'http://127.0.0.1:5000/download'; // **REMEMBER TO CHANGE THIS**
//const dataToSend = {
//    "spotify_url": "https://open.spotify.com/playlist/35lHvGWbIJMJLBNnbu2gLm?si=9lyvAmM8QfGNySvLZ7HplQ"
//};

async function postSpotifyUrl(url, spotifyUrl) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ spotify_url: spotifyUrl })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}. Response: ${errorText}`);
        }

        const result = await response.json();
        console.log('Success:', result);
        return result;

    } catch (error) {
        console.error('There was a problem with the fetch operation:', error.message);
    }
}

// Call the function to send the data

function App() {
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!spotifyUrl) return;
    setLoading(true);
    try {
      const res = await postSpotifyUrl(backendUrl, spotifyUrl);
      console.log('Server response:', res);
    } catch (err) {
      // optionally show UI error
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>download spotify playlists....</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Paste Spotify playlist URL"
            value={spotifyUrl}
            onChange={(e) => setSpotifyUrl(e.target.value)}
            style={{ width: '100%' }}
          />
          <button type="submit" disabled={!spotifyUrl || loading}>
            {loading ? 'Downloading...' : 'Download'}
          </button>
        </form>
      </div>
    </>
  )
}

export default App
