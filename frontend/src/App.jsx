// frontend/src/App.jsx

import React, { useState } from "react";
import axios from "axios";

function App() {
  // ─────────────────────────────────────────────────────────────────────────────
  // 1) If you ever need to override the backend URL (for example, in production),
  //    you can set REACT_APP_API_URL in your environment. Otherwise, we default
  //    to http://localhost:8000.
  // ─────────────────────────────────────────────────────────────────────────────
  const BACKEND_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

  const [code, setCode] = useState("");
  const [review, setReview] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ─────────────────────────────────────────────────────────────────────────────
  // 2) Submit handler: POST to /review on the FastAPI backend
  // ─────────────────────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setReview("");
    setError("");

    // Simple client‐side validation:
    if (!code.trim()) {
      setError("Please enter a code snippet before submitting.");
      return;
    }

    try {
      setLoading(true);

      const payload = {
        code: code,
        max_length: 128, // you can expose these in the UI if you like
        num_beams: 4,
      };

      const resp = await axios.post(
        `${BACKEND_URL}/review`,
        payload,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      // If FastAPI returns a 200 with { review: "…" }, display it:
      setReview(resp.data.review);
    } catch (err) {
      console.error("API call failed:", err);

      // If FastAPI returned JSON with a detail message, show it:
      if (err.response && err.response.data && err.response.data.detail) {
        setError(`Error: ${err.response.data.detail}`);
      } else {
        setError("An error occurred while calling the API.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-lg w-full max-w-xl">
        <h1 className="text-2xl font-bold mb-4 text-center">
          AI-Powered Code Review Assistant
        </h1>

        <form onSubmit={handleSubmit}>
          <textarea
            className="w-full h-48 p-2 border rounded mb-4 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            placeholder="Enter your code snippet..."
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />

          <button
            type="submit"
            className={`bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 focus:outline-none ${
              loading ? "opacity-50 cursor-not-allowed" : ""
            }`}
            disabled={loading}
          >
            {loading ? "Reviewing…" : "Get Review"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-red-600 font-medium">{error}</p>
        )}

        {review && (
          <div className="mt-6 bg-gray-100 p-4 rounded">
            <h2 className="text-lg font-semibold mb-2">Review:</h2>
            <pre className="whitespace-pre-wrap">{review}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
