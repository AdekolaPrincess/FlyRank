# Deploy steps

1. Fill in placeholders. Every [bracketed] bit in the HTML/JS files is
   yours to replace: name, bio, projects, links, agent personality.

2. Save changes, then commit and push from the FlyRank Internship repo root.
   ```
   git add ai-fluency-capstone
   git commit -m "your commit message"
   git push
   ```

3. Deploy on Vercel.
   - Go to vercel.com, sign up with GitHub
   - Add New, Project, select the FlyRank Internship repo
   - In Settings, General, set Root Directory to ai-fluency-capstone
   - Leave build settings on default
   - Deploy

4. Add your API key.
   - Get a free key at aistudio.google.com (sign in with Google, no card required)
   - In Vercel: Settings, Environment Variables
   - Add GEMINI_API_KEY with your key as the value
   - Redeploy from the Deployments tab after saving

5. Test the agent page live. The chat widget only works after
   deployment, since /api/chat does not exist when you open the HTML
   file locally in a browser.

Every commit pushed to the repo triggers a new deploy automatically.
