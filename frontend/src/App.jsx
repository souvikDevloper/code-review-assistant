import { useState } from "react";
import axios from "axios";

export default function App() {
  const [code, setCode] = useState("");
  const [resp, setResp] = useState("");
  const review = async () => {
    setResp("⏳ Reviewing…");
    const { data } = await axios.post("http://localhost:8000/review", { code });
    setResp(data.suggestion);
  };
  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-2">AI Code Review Assistant</h1>
      <textarea
        value={code}
        onChange={e => setCode(e.target.value)}
        rows={12}
        className="w-full border p-2"
        placeholder="Paste code here"
      />
      <button onClick={review} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded">
        Review
      </button>
      {resp && (
        <pre className="mt-4 p-3 bg-gray-100 whitespace-pre-wrap">{resp}</pre>
      )}
    </div>
  );
}
