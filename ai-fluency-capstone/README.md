# Deploy steps

1. **Fill in placeholders.** Every `[bracketed]` bit in the HTML/JS files
   is yours to replace — name, bio, projects, links, agent personality.

2. **Push to GitHub.**
   ```
   git init
   git add .
   git commit -m "first version of site"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

3. **Deploy on Netlify.**
   - Go to netlify.com → "Add new site" → "Import an existing project"
   - Connect your GitHub repo
   - Build settings: leave blank (no build command needed) — Netlify
     will read `netlify.toml` automatically
   - Click Deploy

4. **Add your API key.**
   - Get a free key at aistudio.google.com (sign in with Google, no
     card required)
   - In Netlify: Site configuration → Environment variables
   - Add `GEMINI_API_KEY` with your key as the value
   - Redeploy (Deploys tab → Trigger deploy)

5. **Test the agent page live** — the chat widget only works after
   deployment, since `/.netlify/functions/chat` doesn't exist when you
   just open the HTML file locally in a browser.

That's it — same repo, same deploy, every time you edit a file and push.
