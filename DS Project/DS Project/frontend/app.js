// app.js
// Frontend logic for FPL Scout

// Utility: fetch JSON safely
async function fetchJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
  return resp.json();
}

// Global state
let allPlayers = [];

// DOM elements
const searchInput = document.getElementById('searchInput');
const suggestionsEl = document.getElementById('suggestions');
const playerDetailsEl = document.getElementById('playerDetails');
const themeToggleBtn = document.getElementById('themeToggle');

// Theme handling
function setTheme(isDark) {
  document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  themeToggleBtn.textContent = isDark ? '🌞' : '🌙';
}
function toggleTheme() {
  const isDark = document.documentElement.dataset.theme !== 'dark';
  setTheme(isDark);
}
// Initialize theme from storage
(() => {
  const saved = localStorage.getItem('theme');
  setTheme(saved === 'dark');
})();

themeToggleBtn.addEventListener('click', toggleTheme);

// Fetch player list on load
async function init() {
  try {
    allPlayers = await fetchJSON('/players');
  } catch (e) {
    console.error('Failed to load players:', e);
    alert('Unable to load player data.');
    return;
  }
}
init();

// Simple fuzzy search (case‑insensitive includes)
function filterPlayers(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return allPlayers.filter(p =>
    String(p.player_name).toLowerCase().includes(q) ||
    String(p.team_name).toLowerCase().includes(q)
  ).slice(0, 10); // limit suggestions
}

function renderSuggestions(list) {
  suggestionsEl.innerHTML = '';
  list.forEach(p => {
    const li = document.createElement('li');
    li.textContent = `${p.player_name} – ${p.team_name}`;
    li.dataset.id = p.player_id;
    li.addEventListener('click', () => showPlayerDetails(p.player_id));
    suggestionsEl.appendChild(li);
  });
}

searchInput.addEventListener('input', (e) => {
  const matches = filterPlayers(e.target.value);
  renderSuggestions(matches);
});

async function showPlayerDetails(playerId) {
  // Find basic info
  const player = allPlayers.find(p => p.player_id === playerId);
  if (!player) return;

  // Fetch forecast (default 8 games left)
  let forecast = [];
  try {
    forecast = await fetchJSON(`/forecast/${playerId}`);
  } catch (e) {
    console.warn('Forecast fetch failed:', e);
  }

  // Build UI
  const html = `
    <h2>${player.player_name} <span class="team">${player.team_name}</span></h2>
    <p><strong>Position:</strong> ${player.position}</p>
    <p><strong>Cost:</strong> ${player.now_cost / 10}M</p>
    <p><strong>Points per game:</strong> ${player.points_per_game?.toFixed(2) ?? 'N/A'}</p>
    <h3>Forecast (next ${forecast.length ? forecast.length : 0} games)</h3>
    ${forecast.length ? `<ul>${forecast.map((f, i) => `<li>Game ${i + 1}: ${f.predicted_points?.toFixed(2) ?? '—'} pts</li>`).join('')}</ul>` : '<p>No forecast data.</p>'}
    <button class="close-btn">Close</button>
  `;
  playerDetailsEl.innerHTML = html;
  playerDetailsEl.classList.remove('hidden');
  playerDetailsEl.querySelector('.close-btn').addEventListener('click', () => {
    playerDetailsEl.classList.add('hidden');
    playerDetailsEl.innerHTML = '';
  });
}

// Click outside suggestions to hide them
document.addEventListener('click', (e) => {
  if (!searchInput.contains(e.target) && !suggestionsEl.contains(e.target)) {
    suggestionsEl.innerHTML = '';
  }
});
