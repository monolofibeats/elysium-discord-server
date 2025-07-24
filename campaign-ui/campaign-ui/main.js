let page = 1;
const perPage = 25;            // = 5 × 5 Grid
const selected = new Set();
let maxFollowers = 1000000;
const filters = new Set();
let searchQ = '';
let platformFilter = [];          // Checkboxen
let genreFilter    = [];          // Multiselect
let followerMin = 0;
let followerMax = 1000000;
let priceMin = 0.5;
let priceMax = 100;
let creators = [];
const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("startCampaignBtn");
  if (startBtn) {
    startBtn.addEventListener("click", () => {
      console.log("Kampagne wurde gestartet!");
      startCampaign();
    });
  }

  loadData();
  const priceMinInput = document.getElementById("priceMin");
  const priceMaxInput = document.getElementById("priceMax");
  const followerMinInput = document.getElementById("followerMin");
  const followerMaxInput = document.getElementById("followerMax");

  const priceMinVal = document.getElementById("priceMinVal");
  const priceMaxVal = document.getElementById("priceMaxVal");
  const followerMinVal = document.getElementById("followerMinVal");
  const followerMaxVal = document.getElementById("followerMaxVal");

  priceMinInput.oninput = () => {
    priceMin = parseFloat(priceMinInput.value);
    priceMinVal.textContent = priceMin.toFixed(2) + "€";
    renderGrid();
  };
  priceMaxInput.oninput = () => {
    priceMax = parseFloat(priceMaxInput.value);
    priceMaxVal.textContent = priceMax.toFixed(2) + "€";
    renderGrid();
  };
  followerMinInput.oninput = () => {
    followerMin = parseInt(followerMinInput.value);
    followerMinVal.textContent = followerMin.toLocaleString();
    renderGrid();
  };
  followerMaxInput.oninput = () => {
    followerMax = parseInt(followerMaxInput.value);
    followerMaxVal.textContent = followerMax.toLocaleString();
    renderGrid();
  };

  const maxFollowersEl = $('maxFollowers');
  const maxFollowersInputEl = $('maxFollowersInput');
  const maxPriceEl = $('maxPrice');
  const maxPriceInputEl = $('maxPriceInput');

  $('clearFilters').addEventListener('click', () => {
  $('search').value = '';
  searchQ = '';
  platformFilter = [];
  genreFilter = [];
  followerMax = 1000000;
  maxPrice = 10000;

  // Zurücksetzen aller UI-Elemente
  document.querySelectorAll('.platform-filter').forEach(cb => cb.checked = false);
  $('genreSelect').selectedIndex = -1;
  $('maxFollowers').value = followerMax;
  $('maxFollowersInput').value = followerMax;
  $('maxPrice').value = maxPrice;
  $('maxPriceInput').value = maxPrice;

  page = 1;
  renderGrid();
});

/***** Helper ********************************************************/
function safeLocale(n) {
  return (n ?? 0).toLocaleString();
}

/***** Filtering *****************************************************/
function filtered() {
  return creators.filter(c => {
    if (platformFilter.length && !platformFilter.includes(c.platform)) return false;
    if (genreFilter.length && !c.genres.some(g => genreFilter.includes(g))) return false;
    if (c.followers < followerMin || c.followers > followerMax) return false;
if (c.price < priceMin || c.price > priceMax) return false;

    const q = searchQ.toLowerCase();
    if (
      !c.name.toLowerCase().includes(q) &&
      !c.platform.toLowerCase().includes(q) &&
      !c.genres.some(g => g.toLowerCase().includes(q))
    ) return false;

    return true;
  });
}

function getDelta(current, last) {
  const change = ((current - last) / Math.max(1, last)) * 100;
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(1)}%`;
}
function compareUpload(curr, last) {
  return curr > last ? '↑' : curr < last ? '↓' : '=';
}

  function renderSummary() {
  const selectedArray = [...selected].map(id => creators.find(c => c.id === id));
  const totalCost = selectedArray.reduce((sum, c) => sum + (c.price || 0), 0);
  const totalFollowers = selectedArray.reduce((sum, c) => sum + (c.followers || 0), 0);
  const totalViews = selectedArray.reduce((sum, c) => sum + (c.views30d || 0), 0);

  if ($('selectedCount')) $('selectedCount').textContent = selectedArray.length;
  if ($('totalCost')) $('totalCost').textContent = totalCost.toLocaleString();
  if ($('totalFollowers')) $('totalFollowers').textContent = totalFollowers.toLocaleString();
  if ($('totalViews')) $('totalViews').textContent = totalViews.toLocaleString();
  if ($('selectedCountOverview')) $('selectedCountOverview').textContent = selectedArray.length;
  if ($('totalFollowersOverview')) $('totalFollowersOverview').textContent = totalFollowers.toLocaleString();
  if ($('totalViewsOverview')) $('totalViewsOverview').textContent = totalViews.toLocaleString();
}

/***** Rendering *****************************************************/
function renderGrid() {
  const followerRef = 100000;
  const priceRef = 25;
  const grid = $('creator-grid');
  grid.innerHTML = '';
  const data = filtered();
  const maxViews = data.length ? Math.max(...data.map(c => c.views30d || 1)) : 1;
  const max = Math.ceil(data.length / perPage);
  page = Math.min(page, max);

  const slice = data.slice((page - 1) * perPage, page * perPage);

  slice.forEach((c) => {
    const uploadsDisplay = typeof c.uploadsThisMonth === 'number'
      ? `${c.uploadsThisMonth} (${compareUpload(c.uploadsThisMonth, c.uploadsLastMonth)})`
      : '–';

    const card = document.createElement('div');
    card.className = `creator-card ${selected.has(c.id) ? 'selected' : ''}`;
    card.onclick = () => toggleSelection(c.id);

    card.innerHTML = `
  <img class="creator-img" src="${c.image}" alt="${c.name}">
  <div class="creator-name">${c.name}</div>
  <div class="creator-info text-sm text-gray-400 mb-1">${c.platform}</div>

  <div class="stars mb-1">
    ${'★'.repeat(c.rating || 0)}${'☆'.repeat(5 - (c.rating || 0))}
    <span class="ml-1 text-xs text-gray-400">(${c.rating ?? 0} ST)</span>
  </div>

  <div class="info-section">
    <div class="bar-title">Follower:</div>
<div class="bar"><div class="fill" style="width: ${(Math.min(c.followers / followerRef, 1)) * 100}%; background-color: ${c.followers < followerRef * 0.5 ? '#f87171' : c.followers > followerRef * 1.5 ? '#4ade80' : '#facc15'}"></div></div>
    <div class="bar-label">${safeLocale(c.followers)} total</div>

    <div class="bar-title">Views (30d):</div>
    <div class="bar"><div class="fill" style="width: ${(c.views30d / maxViews) * 100}%"></div></div>
    <div class="bar-label">${safeLocale(c.views30d)} (${c.viewsGrowth ?? 0}% vs. Vormonat)</div>

    <div class="bar-title">Uploads:</div>
    <div class="bar"><div class="fill" style="width: ${(c.uploadsThisMonth / Math.max(1, c.uploadsLastMonth || 1)) * 100}%"></div></div>
    <div class="bar-label">
  ${typeof c.uploadsThisMonth === 'number' ? c.uploadsThisMonth : '–'} this month
  (${typeof c.uploadsThisMonth === 'number' && typeof c.uploadsLastMonth === 'number'
    ? compareUpload(c.uploadsThisMonth, c.uploadsLastMonth)
    : '–'})
</div>

    <div class="bar-title">Preis (€):</div>
<div class="bar"><div class="fill" style="width: ${(Math.min(c.price / priceRef, 2)) * 100}%; background-color: ${c.price < priceRef * 0.5 ? '#4ade80' : c.price > priceRef * 2 ? '#f87171' : '#facc15'}"></div></div>
    <div class="bar-label">${c.price ?? 0} €</div>

    <div class="mt-2 text-xs text-gray-500">Genres: ${c.genres?.join(', ') || '–'}</div>
    <button data-id="${c.id}" class="text-sm text-blue-500 underline note-button">Note</button>
    <div id="note-${c.id}" class="mt-2 text-xs text-yellow-800 italic">${c.adminNote ?? ''}</div>
  </div>

  <a href="${c.link}" class="creator-link" target="_blank">Profil öffnen</a>
`;
    grid.appendChild(card);
  });

  const notes = JSON.parse(localStorage.getItem('creatorNotes') || '[]');
notes.forEach(({ id, note }) => {
  const el = document.getElementById(`note-${id}`);
  if (el) el.textContent = note;
});

  renderPagination(max);
  renderSummary();

  document.querySelectorAll('.note-button').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.id;
    const note = prompt("Admin Note für diesen Creator eingeben:");
    if (note !== null) {
      const creator = creators.find(c => c.id === id);
      if (creator) {
        creator.adminNote = note;
        const notes = creators
          .filter(c => c.adminNote && c.adminNote.trim() !== '')
          .map(c => ({ id: c.id, note: c.adminNote }));
        localStorage.setItem('creatorNotes', JSON.stringify(notes));
        document.getElementById(`note-${id}`).textContent = note;
      }
    }
  });
});

}
/***** Pagination ****************************************************/
$('prevPage').onclick = () => {
  if (page > 1) page--;
  renderGrid();
};

$('nextPage').onclick = () => {
  if (page * perPage < filtered().length) page++;
  renderGrid();
};

/***** Filter-Buttons ***********************************************/
document.querySelectorAll('.chip').forEach(btn => {
  btn.onclick = () => {
    const k = btn.dataset.filter;
    btn.classList.toggle('active');
    filters.has(k) ? filters.delete(k) : filters.add(k);
    page = 1;
    renderGrid();
  };
});

/***** Suche *********************************************************/
$('search').oninput = (e) => {
  searchQ = e.target.value.trim().toLowerCase();
  page = 1;
  renderGrid();
};

/***** Campaign Overview *********************************************/
function updateOverview() {
  const box   = $('campaignOverview');
  const list  = $('selectedCreatorsList');
  const stats = {
    count:   $('selectedCount'),
    cost:    $('totalCost'),
    reach:   $('totalFollowers'),
    views:   $('totalViews'),
  };

  if (!box) return;

  const sel = [...selected].map(id => creators.find(c => c.id === id));
  if (sel.length === 0) {
    box.classList.add('hidden');
    return;
  }

  list.innerHTML = sel
    .map(c => `<li>${c.name} (${c.platform}) – ${c.price} €</li>`)
    .join('');

  const budget  = sel.reduce((sum, c) => sum + c.price, 0);
  const reach   = sel.reduce((sum, c) => sum + c.followers, 0);
  const views30 = sel.reduce((sum, c) => sum + c.views30d, 0);

  stats.count.textContent  = sel.length;
  stats.cost.textContent   = budget.toLocaleString('de-DE');
  stats.reach.textContent  = reach.toLocaleString('de-DE');
  stats.views.textContent  = views30.toLocaleString('de-DE');

  box.classList.remove('hidden');

$('selectedCountOverview').textContent = sel.length;
$('totalCost').textContent = budget.toLocaleString('de-DE');
$('totalFollowersOverview').textContent = reach.toLocaleString('de-DE');
$('totalViewsOverview').textContent = views30.toLocaleString('de-DE');

}

/*** Plattform-Checkboxen ***/
document.querySelectorAll('.platform-filter').forEach(cb => {
  cb.addEventListener('change', () => {
    platformFilter = Array.from(document.querySelectorAll('.platform-filter:checked')).map(cb => cb.value);
    page = 1;
    renderGrid();
  });
});

/*** Follower Slider ***/
$('maxFollowers').addEventListener('input', (e) => {
  followerMax = parseFloat(e.target.value);
  $('maxFollowersInput').value = followerMax;
  page = 1;
  renderGrid();
});

$('maxFollowersInput').addEventListener('input', (e) => {
  followerMax = parseFloat(e.target.value);
  $('maxFollowers').value = followerMax;
  page = 1;
  renderGrid();
});

/*** Genre-Multiselect ***/
$('genreSelect').addEventListener('change', () => {
  genreFilter = Array.from($('genreSelect').selectedOptions).map(opt => opt.value);
  page = 1;
  renderGrid();
});

async function startCampaign() {
    const startBtn = document.getElementById("startCampaignBtn");
    startBtn.disabled = true;

    const customMessage = document.getElementById("customMessage")?.value || "";

    try {
        console.log("Kampagne wurde gestartet!");

        const selectedCreators = creators.filter(c => selected.has(c.id));
        const payload = {
            creators: selectedCreators,
            message: customMessage
        };

        const response = await fetch("/start-campaign", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            console.error("Fehler beim Kampagnenstart:", response.status, response.statusText);
            alert("⚠️ Netzwerkfehler beim Kampagnenstart.");
        }
    } catch (error) {
        console.error("Fehler bei startCampaign:", error);
        alert("⚠️ Fehler beim Kampagnenstart.");
    } finally {
        startBtn.disabled = false;
    }
}

/***** Kick-off ******************************************************/

async function loadData() {
  const response = await fetch('submissions.json');
  const data = await response.json();
  creators = Array.isArray(data) ? data : (data.creators || []);
  renderGrid();
  updateOverview();
}

function renderPagination(maxPages) {
  $('currentPage').textContent = `Seite ${page} / ${maxPages}`;
}

function toggleSelection(id) {
  if (selected.has(id)) {
    selected.delete(id);
  } else {
    selected.add(id);
  }
  renderGrid();
  updateOverview(); // ← Wichtig!
}

function editNote(id) {
  const note = prompt("Admin Note für diesen Creator eingeben:");
  if (note !== null) {
    const creator = creators.find(c => c.id === id);
    if (creator) {
      creator.adminNote = note;

      const notes = creators
        .filter(c => c.adminNote && c.adminNote.trim() !== '')
        .map(c => ({ id: c.id, note: c.adminNote }));
      localStorage.setItem('creatorNotes', JSON.stringify(notes));
      document.getElementById(`note-${id}`).textContent = note;

      renderGrid(); // ← wichtig, damit das Note-Feld neu gerendert wird
    }
  }
}

});