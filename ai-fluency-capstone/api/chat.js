// This runs on Vercel's servers, not in the browser — so your API
// key stays hidden. Uses Google's Gemini API, free tier, no card
// needed. Get a key at aistudio.google.com and set GEMINI_API_KEY
// in Vercel's dashboard under Settings → Environment Variables.

const SYSTEM_PROMPT = "You are the personal agent of Princess, built as part of an AI fluency capstone project. Help visitors learn about their background, skills, and the projects listed on this site. Answer questions clearly and concisely, in a friendly but professional tone. If you don't know something specific about them, say so honestly rather than guessing.";

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ reply: 'Method not allowed' });
  }

  try {
    const { message } = req.body;

    const response = await fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': process.env.GEMINI_API_KEY
        },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
          contents: [{ role: 'user', parts: [{ text: message }] }]
        })
      }
    );

    const data = await response.json();
    const reply =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      "Sorry, I couldn't generate a reply.";

    res.status(200).json({ reply });
  } catch (err) {
    res.status(500).json({ reply: 'Server error: ' + err.message });
  }
};
