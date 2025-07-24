const puppeteer = require('puppeteer-core');

async function scrapeSpotifyPlaylist(url) {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  });

  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2' });

  // 3 Sekunden warten, damit Inhalte laden
  await new Promise(r => setTimeout(r, 3000));

  // Alle Spans durchgehen und nach Likes-Text suchen
// Statt: const likesElement = await page.$('span:has-text("likes")');
const elementWithSaves = await page.waitForSelector('span', { timeout: 10000 });
const allText = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('span'))
    .map(e => e.textContent)
    .find(text => text && text.toLowerCase().includes('saves'));
});

// Extrahiere die Zahl
let saves = null;
if (allText) {
  const match = allText.match(/([\d.,]+)\s*Saves/i);
  if (match) {
    saves = match[1].replace(/\./g, '').replace(',', '.'); // z. B. "235.620" → "235620"
  }
}

if (saves) {
  console.log(`📌 Playlist Saves: ${saves}`);
} else {
  console.log("❌ Saves nicht gefunden – evtl. andere Sprache oder Layout?");
}

  await browser.close();
}

scrapeSpotifyPlaylist('https://open.spotify.com/playlist/37i9dQZF1DX2PQDq3PdrHQ?si=7ec0f0d84e764ce6');
