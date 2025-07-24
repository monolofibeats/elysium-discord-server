// update_spotify_stats.js
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

// ---------- SETTINGS ----------
const JSON_FILE = 'submissions.json';
const WAIT_MS   = 3500;              // 3,5 s – reicht meist fürs Nachladen
const CHROME    = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
// --------------------------------

async function getPlaylistSaves(url) {
  const browser = await puppeteer.launch({ headless: true, executablePath: CHROME });
  const page    = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, WAIT_MS));

  const saves = await page.evaluate(() => {
    const text = Array.from(document.querySelectorAll('span'))
      .map(el => el.textContent.toLowerCase())
      .find(t => t.includes('saves'));
    if (!text) return null;
    const m = text.match(/([\d.,]+)/);
    return m ? parseInt(m[1].replace(/[.,]/g, ''), 10) : null;
  });

  await browser.close();
  return saves;
}

// ---------- MAIN ------------
(async () => {
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const data  = fs.existsSync(JSON_FILE)
    ? JSON.parse(fs.readFileSync(JSON_FILE, 'utf-8'))
    : {};

  if (!data.spotify) {
    console.log('⚠️  Keine Spotify-Playlists in submissions.json gefunden.');
    process.exit(0);
  }

  for (const playlistId of Object.keys(data.spotify)) {
    const url   = `https://open.spotify.com/playlist/${playlistId}`;
    const saves = await getPlaylistSaves(url);

    if (!saves) {
      console.log(`❌  ${playlistId}: Saves nicht gefunden`);
      continue;
    }

    // Pfad anlegen & speichern
    const pl = data.spotify[playlistId];
    if (!pl.saves) pl.saves = {};
    pl.saves[today] = saves;
    // Optional: Wachstum zum letzten Eintrag berechnen
    const saveDates = Object.keys(saves).sort();
    if (saveDates.length > 1) {
      const prevDate = saveDates[saveDates.length - 2];
      const prevValue = saves[prevDate];
      playlistEntry["monthly_gain"] = currentSaves - prevValue;
    }


    console.log(`✅  ${playlistId}: ${saves} Saves eingetragen`);
  }

  fs.writeFileSync(JSON_FILE, JSON.stringify(data, null, 2));
  console.log('📝  submissions.json aktualisiert');
})();
