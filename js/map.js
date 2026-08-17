// js/map.js
// Loads data/gyms.json (compiled from gyms/*.md by scripts/build.js) and
// renders it as a Leaflet map + synced sidebar list.

const DISCIPLINE_COLOR = {
  boulder: "#e8631c",
  toprope: "#2f7de1",
  lead: "#2e9e5b",
  speed: "#dd0d0d",
};
const UNVISITED_COLOR = "#565c63";
const OUTDOOR_WALL_COLOR = "#bd197e";
const DISCIPLINE_LABEL = { boulder: "Boulder", toprope: "Toprope", lead: "Lead", speed: "Speed" };

// Roughly frames the Netherlands, Belgium, and the sliver of Germany
// around Limburg (Aachen / Aachen-Maastricht corridor).
const MAP_CENTER = [51.15, 5.3];
const MAP_ZOOM = 8;
const MAP_BOUNDS = [
  [49.4, 2.2], // SW
  [53.7, 7.4], // NE
];

let map;
let markerLayer;
let gyms = [];
let activeDisciplines = new Set(); // empty = all disciplines shown
let hasOutdoorWall = false;
let visitedOnly = false;
let checkedOnly = false;
let markersBySlug = new Map();

async function loadGyms() {
  const res = await fetch("data/gyms.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load data/gyms.json (${res.status})`);
  return res.json();
}

function holdMarkerHtml(gym) {
  const colors = gym.visited
    ? gym.discipline.map((d) => DISCIPLINE_COLOR[d])
    : [UNVISITED_COLOR];
  const n = colors.length;
  const stripeH = 28 / n;
  const stripes = colors
    .map((c, i) => `<rect x="0" y="${i * stripeH}" width="24" height="${stripeH + 0.5}" fill="${c}" />`)
    .join("");
  const checkedColor = !gym.checked ? "#14171a": "#0e7c45";
  return `
    <svg width="24" height="28" viewBox="0 0 24 28" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <clipPath id="clip-${gym.slug}">
          <path d="M12 27 C 5 22, 1 16, 1 10 C 1 4.5, 6 1, 12 1 C 18 1, 23 4.5, 23 10 C 23 16, 19 22, 12 27 Z"/>
        </clipPath>
      </defs>
      <g clip-path="url(#clip-${gym.slug})">${stripes}</g>
      <path d="M12 27 C 5 22, 1 16, 1 10 C 1 4.5, 6 1, 12 1 C 18 1, 23 4.5, 23 10 C 23 16, 19 22, 12 27 Z"
            fill="none" stroke="${checkedColor}" stroke-width="1.5"/>
    </svg>`;
}

function makeIcon(gym) {
  const cls = "hold-marker" + (gym.visited ? "" : " hold-marker--unvisited");
  return L.divIcon({
    html: holdMarkerHtml(gym),
    className: cls,
    iconSize: [24, 28],
    iconAnchor: [12, 27],
    popupAnchor: [0, -24],
  });
}

function pillsHtml(gym) {
  return gym.discipline
    .map((d) => {
      const bg = gym.visited ? DISCIPLINE_COLOR[d] : UNVISITED_COLOR;
      return `<span class="pill" style="background:${bg}">${DISCIPLINE_LABEL[d]}</span>`;
    })
    .join("");
}

function checkBadgeHtml(gym) {
  if (!gym.checked) return "";
  return `<span class="check-badge" title="Confirmed against the gym's own website">✓</span>`;
}

function popupHtml(gym) {
  const place = [gym.city, gym.country].filter(Boolean).join(", ");
  const meta = [
    gym.visited ? (gym.lastVisit ? `Last visit ${gym.lastVisit}` : "Visited") : "Not visited yet",
    gym.rating ? `${gym.rating}/5` : null,
    gym.checked ? "" : "Unverified",
  ]
    .filter(Boolean)
    .join(" · ");

  return `
    <p class="popup__name">${gym.name}${checkBadgeHtml(gym)}</p>
    <p class="popup__place">${place}</p>
    <div class="popup__pills">${pillsHtml(gym)}</div>
    ${gym.notes ? `<p class="popup__notes">${gym.notes.replace(/\n/g, "<br>")}</p>` : ""}
    <p class="popup__meta">${meta}</p>
    ${gym.website ? `<p class="popup__link"><a href="${gym.website}" target="_blank" rel="noopener">${new URL(gym.website).hostname} ↗</a></p>` : ""}
  `;
}

function passesFilters(gym) {
  if (gym.name == "The Climbing Corner")console.log(checkedOnly, !gym.checked,!visitedOnly,gym.visited, gym)
  if (hasOutdoorWall && !gym.hasOutdoorWall) return false;
  if (visitedOnly && !gym.visited) return false;
  if (checkedOnly && !gym.checked) { return false }
  else if (checkedOnly && !visitedOnly && gym.visited) return false;
  if (activeDisciplines.size === 0) return true;
  return gym.discipline.some((d) => activeDisciplines.has(d));
}

function renderMarkers() {
  markerLayer.clearLayers();
  markersBySlug.clear();
  gyms.filter(passesFilters).forEach((gym) => {
    const marker = L.marker([gym.lat, gym.lon], { icon: makeIcon(gym) })
      .bindPopup(popupHtml(gym))
      .addTo(markerLayer);
    marker.on("click", () => setActiveCard(gym.slug));
    markersBySlug.set(gym.slug, marker);
  });
}

function renderStats() {
  const el = document.getElementById("stats");
  const counts = { boulder: 0, toprope: 0, lead: 0, speed: 0 };
  gyms.filter(passesFilters).forEach((g) => {
    g.discipline.forEach((d) => (counts[d] += 1));
  });
  el.innerHTML = Object.entries(counts)
    .map(
      ([d, count]) => `
      <div class="stat">
        <span class="stat__dot" style="background:${DISCIPLINE_COLOR[d]}"></span>
        <span class="stat__count">${count}</span>
        <span class="stat__label">${DISCIPLINE_LABEL[d]}</span>
      </div>`
    )
    .join("");
}

function renderFilters() {
  const el = document.getElementById("filters");
  const disciplineChips = Object.keys(DISCIPLINE_COLOR)
    .map(
      (d) => `
      <button class="filter-chip" data-kind="discipline" data-value="${d}" data-active="false">
        <span class="filter-chip__dot" style="background:${DISCIPLINE_COLOR[d]}"></span>${DISCIPLINE_LABEL[d]}
      </button>`
    )
    .join("");

  el.innerHTML =
    disciplineChips +
    `<button class="filter-chip" data-kind="hasOutdoorWall" data-active="false">
       <span class="filter-chip__dot" style="background:${OUTDOOR_WALL_COLOR}"></span>Has outdoor wall
     </button>
     <button class="filter-chip" data-kind="visited" data-active="false">
       <span class="filter-chip__dot" style="background:${UNVISITED_COLOR}"></span>Visited only
     </button>
     <button class="filter-chip" data-kind="checked" data-active="false">
       <span class="filter-chip__dot filter-chip__dot--check">✓</span>On list
     </button>`;

  el.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const isActive = chip.getAttribute("data-active") === "true";
      chip.setAttribute("data-active", String(!isActive));
      if (chip.dataset.kind === "discipline") {
        const v = chip.dataset.value;
        isActive ? activeDisciplines.delete(v) : activeDisciplines.add(v);
      } else if (chip.dataset.kind === "visited") {
        visitedOnly = !isActive;
      } else if (chip.dataset.kind === "checked") {
        checkedOnly = !isActive;
      } else if (chip.dataset.kind === "hasOutdoorWall") {
        hasOutdoorWall = !isActive;
      }
      renderStats();
      renderMarkers();
      renderList();
    });
  });
}

function setActiveCard(slug) {
  document.querySelectorAll(".gym-card").forEach((c) => c.removeAttribute("data-active"));
  const card = document.querySelector(`.gym-card[data-slug="${slug}"]`);
  if (card) {
    card.setAttribute("data-active", "true");
    card.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function focusGym(gym) {
  map.flyTo([gym.lat, gym.lon], Math.max(map.getZoom(), 12), { duration: 0.6 });
  const marker = markersBySlug.get(gym.slug);
  if (marker) marker.openPopup();
  setActiveCard(gym.slug);
}

function renderList() {
  const el = document.getElementById("gym-list");
  const visible = gyms.filter(passesFilters).sort((a, b) => a.name.localeCompare(b.name));

  if (visible.length === 0) {
    el.innerHTML = `<li class="empty-state">No gyms match these filters.</li>`;
    return;
  }

  el.innerHTML = visible
    .map(
      (gym) => `
      <li class="gym-card${gym.visited ? "" : " gym-card--unvisited"}" data-slug="${gym.slug}" tabindex="0" role="button">
        <div class="gym-card__top">
          <span class="gym-card__name">${gym.name}${checkBadgeHtml(gym)}</span>
        </div>
        <div class="gym-card__place">${[gym.city, gym.country].filter(Boolean).join(", ")}</div>
        <div class="gym-card__pills">${pillsHtml(gym)}</div>
      </li>`
    )
    .join("");

  el.querySelectorAll(".gym-card").forEach((card) => {
    const gym = gyms.find((g) => g.slug === card.dataset.slug);
    const activate = () => focusGym(gym);
    card.addEventListener("click", activate);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(); }
    });
  });
}

// Chalk-line trail: a dashed line through visited gyms in chronological
// order (by lastVisit), like a big multi-pitch route across the Benelux.
function renderTrail() {
  const trailPoints = gyms
    .filter((g) => g.visited && g.lastVisit)
    .sort((a, b) => a.lastVisit.localeCompare(b.lastVisit))
    .map((g) => [g.lat, g.lon]);

  if (trailPoints.length > 1) {
    L.polyline(trailPoints, {
      color: "#9aa0a6",
      weight: 1.5,
      opacity: 0.55,
      dashArray: "2 7",
      lineCap: "round",
    }).addTo(map);
  }
}

async function init() {
  map = L.map("map", { zoomControl: true, minZoom: 6, maxZoom: 18 })
    .setView(MAP_CENTER, MAP_ZOOM)
    .fitBounds(MAP_BOUNDS);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);

  try {
    gyms = await loadGyms();
  } catch (err) {
    document.getElementById("gym-list").innerHTML =
      `<li class="empty-state">Couldn't load data/gyms.json.<br>Run <code>npm run build</code> first.</li>`;
    console.error(err);
    return;
  }

  renderStats();
  renderFilters();
  renderMarkers();
  renderList();
  renderTrail();
}

init();
