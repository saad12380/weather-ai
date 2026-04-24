# Weather AI Website

## Overview
This folder contains the static marketing website for the Weather Anomaly Predictor platform. It is designed to showcase the platform's features, documentation, pricing, demo pages, and company information.

## Website Contents
- `index.html` — Landing page with product overview and calls to action
- `features.html` — Detailed product features and benefits
- `pricing.html` — Pricing plans and subscription details
- `demo.html` — Interactive demo and feature showcase
- `docs.html` — API and integration documentation pages
- `blog/` — Blog posts and content pages
- `components/` — Reusable HTML snippets for header, footer, navbar, and testimonials
- `assets/` — Images, CSS, JavaScript, fonts, and static assets
- `styles/` — Additional CSS styling files
- `PHPMailer/` — PHP mailer library included for contact form use

## Tech Stack
- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Chart.js
- Font Awesome icons
- Static site generator-friendly layout

## Local Development
Install dependencies and run the site using `npm`:

```powershell
cd weather-anomaly-predictor\weather-ai-website
npm install
npm run dev
```

This starts a local development server with live reload, typically on `http://localhost:3000`.

## Build and Deployment
The website includes scripts for basic production tasks:

```powershell
npm run build
npm run minify:css
npm run minify:js
npm run deploy
```

- `build` is a placeholder for site build tasks.
- `minify:css` combines and compresses CSS files.
- `minify:js` compresses JavaScript assets.
- `deploy` publishes the site to GitHub Pages using `gh-pages`.

## Usage
Use this site as the public-facing marketing site for your platform. It integrates with the backend API for feature demos and contact forms, while providing a polished landing experience for visitors.

## Notes
- Update the static pages to match your project branding and messaging.
- Replace placeholder content with actual product details, screenshots, and links.
- Ensure the backend API endpoints are available if demo pages or contact forms rely on them.

## Author
Weather AI Platform

## License
MIT
