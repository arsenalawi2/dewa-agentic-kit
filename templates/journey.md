# Journey Page Template

Create a `/journey` route that tells the story of the project — what problem it solves, how it works, and what makes it impressive.

## Data Source

**Primary (auto-updated):** Fetch from `/journey-data.json` in the project's public directory. This file is maintained by Claude Code during sessions — it reads the codebase and session context to generate narrative content automatically.

```javascript
const res = await fetch('/journey-data.json')
const journey = await res.json()
```

### journey-data.json Schema

```json
{
  "project_name": "My Project",
  "tagline": "One-line description of what this project does",
  "hero_stats": [
    { "value": "113K+", "label": "items tracked" },
    { "value": "8", "label": "AI domains" }
  ],
  "challenge": {
    "title": "The Problem",
    "description": "2-3 sentences about what pain point this solves",
    "stats": [
      { "value": "100+", "label": "daily updates to track" }
    ]
  },
  "how_it_works": {
    "title": "How It Works",
    "steps": [
      { "step": 1, "title": "Collect", "description": "What data sources feed in" },
      { "step": 2, "title": "Process", "description": "What transformation happens" },
      { "step": 3, "title": "Enrich", "description": "Any AI/ML augmentation" },
      { "step": 4, "title": "Visualize", "description": "How users see the result" }
    ]
  },
  "features": [
    { "title": "Feature Name", "description": "What it does in 1-2 sentences" }
  ],
  "tech_stats": {
    "api_endpoints": 34,
    "database_tables": 12,
    "languages_supported": 2
  },
  "updated_at": "2025-04-10T14:30:00"
}
```

### Rules for Generating Journey Data
- Write in active voice, present tense
- Lead with impact, not implementation details
- Every stat should be real and verifiable from the code
- Keep descriptions concise — the page is visual, not documentation
- Update `updated_at` every time you modify this file
- If journey-data.json already exists, UPDATE it — don't overwrite unless the project fundamentally changed
- Generate by reading: project code structure, README.md, PROJECT.md, and what was built in the current session

## Purpose

This page is a narrative showcase. It's what you show stakeholders, present in meetings, or share on social media. It answers: "What is this and why should I care?"

## Page Structure

Use the EZ Design System. Sections flow vertically with alternating backgrounds.

### 1. Hero Section
- Large project name in the display font (32-48px)
- One-line description of what the project does
- Stats row: 3-5 key metrics (e.g., "113K+ items tracked", "8 AI domains", "3 data sources")
- Optional: subtle background pattern or gradient

### 2. The Challenge
- Section title: "The Problem" or "The Challenge"
- 2-3 sentences explaining what pain point this project solves
- Optional: visual showing the before state (complexity, manual work, scattered data)
- Stats showing the scale of the problem (e.g., "100+ daily updates", "30+ data sources")

### 3. How It Works
- Section title: "How It Works" or "The Solution"
- 3-4 step pipeline visualization:
  1. **Collect** — where data comes from
  2. **Process** — what transformation happens
  3. **Enrich** — any AI/ML augmentation
  4. **Visualize** — how users interact with the result
- Each step gets an icon/number, a title, a short description, and key stats

### 4. Features Showcase
- Grid of 3-6 key features
- Each feature: icon + title + 1-2 sentence description
- Use the EZ Design System's interactive card pattern

### 5. Technical Stats (optional)
- API endpoints count
- Database tables/records
- Languages supported
- Integration points
- Performance metrics

### 6. Built With AI Footer
- Link to the /vibe-code page
- Brief mention: "This entire project was built using Claude Code"
- Small stats preview (prompts, cost, active hours)

## Design Notes
- Hero should be visually impactful — this is the first impression
- Use the section pattern: uppercase label (10px, accent) + heading (24px) + description + content
- Stats use 56px values in accent color with 16px labels below
- 3-column responsive grids with 24px gaps
- Alternate bg-primary / bg-secondary between sections
- Keep text concise — this is a visual page, not documentation
- Cross-link to /vibe-code page prominently

## Content Guidelines
- Write in active voice, present tense
- Lead with impact, not implementation details
- Every stat should make the reader go "wow"
- The page should work as a standalone pitch — no prior context needed
