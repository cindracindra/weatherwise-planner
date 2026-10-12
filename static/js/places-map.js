/*
 * The places map: a pin per place, marked with how it suits today's
 * weather (a glyph as well as a colour), and a card for each pin with
 * Google Maps links. The place form can set its pin by address search
 * (through our server, which paces requests to Nominatim) or, in
 * "Choose on the map" mode, by clicking the map.
 *
 * Tiles: OpenStreetMap's, muted by the stylesheet. No API key.
 */
(() => {
  const el = document.querySelector("[data-map]");
  const dataEl = document.getElementById("places-data");
  if (!el || !dataEl || !window.L) return;

  const data = JSON.parse(dataEl.textContent);
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LONDON = [51.509, -0.118];
  const GLYPH = { great: "check", okay: "minus", poor: "x", none: "circle" };

  const map = L.map(el, {
    center: LONDON,
    zoom: 11,
    scrollWheelZoom: false, // the page scrolls past the map; use + and -
    zoomAnimation: !still,
    fadeAnimation: !still,
    markerZoomAnimation: !still,
  });
  // OpenStreetMap's own tiles: free for light use with this attribution.
  // The stylesheet mutes their colours to sit on the page.
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  function pinIcon(fit, extra) {
    const kind = fit || "none";
    return L.divIcon({
      className: "",
      html: `<span class="pin pin--${kind}${extra || ""}"><i class="ph-bold ph-${GLYPH[kind]}" aria-hidden="true"></i></span>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -14],
    });
  }

  function text(tag, cls, value) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    node.textContent = value;
    return node;
  }

  function link(href, label) {
    const a = text("a", "card__link", label);
    a.href = href;
    if (/^https:/.test(href)) {
      a.target = "_blank";
      a.rel = "noopener";
    }
    return a;
  }

  // The card a pin opens: built from text nodes, never HTML strings
  function card(p) {
    const box = document.createElement("div");
    box.className = "card";
    box.append(text("strong", "card__name", p.name));
    box.append(text("span", "card__meta", [p.category, p.address].filter(Boolean).join(", ")));
    const today = text("span", `card__fit fit fit--${p.fit || "none"}`,
      p.fit ? `Today: ${p.fit_label}` : p.today_note);
    box.append(today);
    if (p.fit_why) box.append(text("span", "card__why", p.fit_why));
    if (p.next) box.append(text("span", "card__why", `Next great: ${p.next}`));
    const links = document.createElement("span");
    links.className = "card__links";
    links.append(link(p.maps_url, "Google Maps"), link(p.directions_url, "Directions"), link(p.edit_url, "Edit"));
    box.append(links);
    return box;
  }

  const bounds = [];
  let selectedMarker = null;
  data.places.forEach((p) => {
    if (p.latitude === null || p.longitude === null) return;
    const label = `${p.name}: ${p.fit ? p.fit_label + " today" : p.today_note.toLowerCase()}`;
    const marker = L.marker([p.latitude, p.longitude], {
      icon: pinIcon(p.fit, p.id === data.selected ? " pin--selected" : ""),
      title: label,
      alt: label,
      keyboard: true,
      riseOnHover: true,
    }).addTo(map);
    marker.bindPopup(() => card(p), { maxWidth: 280 });
    bounds.push([p.latitude, p.longitude]);
    if (p.id === data.selected) selectedMarker = marker;
  });

  if (selectedMarker) {
    map.setView(selectedMarker.getLatLng(), 14, { animate: false });
  } else if (bounds.length) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14, animate: false });
  }

  // ---------- Setting the pin from the form ----------

  const field = document.querySelector("[data-pin-field]");
  if (!field) return;
  const lat = field.querySelector("[data-lat]");
  const lng = field.querySelector("[data-lng]");
  const state = field.querySelector("[data-pin-state]");
  const query = field.querySelector("[data-pin-q]");
  const results = field.querySelector("[data-pin-results]");
  const pick = field.querySelector("[data-pin-pick]");
  const form = field.closest("form");
  field.querySelectorAll("[data-pin-tools]").forEach((n) => { n.hidden = false; });

  let draft = null;
  function setPin(latitude, longitude, note) {
    lat.value = latitude.toFixed(6);
    lng.value = longitude.toFixed(6);
    if (!draft) {
      draft = L.marker([latitude, longitude], {
        icon: pinIcon(null, " pin--draft"), title: "The new pin", alt: "The new pin", keyboard: false,
      }).addTo(map);
    } else {
      draft.setLatLng([latitude, longitude]);
    }
    map.setView([latitude, longitude], Math.max(map.getZoom(), 15), { animate: !still });
    state.textContent = note || "Pinned. Save the place to keep it.";
  }

  function clearPin() {
    lat.value = "";
    lng.value = "";
    if (draft) { draft.remove(); draft = null; }
    state.textContent = "No pin. Save the place to remove it.";
  }

  function setPicking(on) {
    pick.setAttribute("aria-pressed", on ? "true" : "false");
    el.classList.toggle("map__canvas--picking", on);
    if (on) state.textContent = "Click the map where the place is.";
  }

  pick.addEventListener("click", () => {
    const on = pick.getAttribute("aria-pressed") !== "true";
    setPicking(on);
    if (on) el.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "center" });
  });
  map.on("click", (e) => {
    if (pick.getAttribute("aria-pressed") !== "true") return;
    setPicking(false);
    setPin(e.latlng.lat, e.latlng.lng);
  });
  field.querySelector("[data-pin-clear]").addEventListener("click", clearPin);

  // Address search: only when asked (Nominatim allows no search-as-you-type)
  async function search() {
    const q = query.value.trim();
    results.replaceChildren();
    if (q.length < 3) {
      state.textContent = "Type at least three letters of the address.";
      return;
    }
    state.textContent = "Searching…";
    try {
      const response = await fetch(`/places/search?q=${encodeURIComponent(q)}`, {
        headers: { Accept: "application/json" },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error);
      if (!body.results.length) {
        state.textContent = "Nothing found in London. Try another spelling, or choose on the map.";
        return;
      }
      state.textContent = `${body.results.length} found. Choose one.`;
      body.results.forEach((r) => {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pin-field__result";
        button.append(text("strong", "", r.name), text("span", "", r.short));
        button.addEventListener("click", () => {
          const name = form.querySelector('[name="name"]');
          const address = form.querySelector('[name="address"]');
          if (!name.value.trim()) name.value = r.name.slice(0, 60);
          if (!address.value.trim()) address.value = r.short.slice(0, 200);
          results.replaceChildren();
          setPin(r.latitude, r.longitude, `Pinned at ${r.name}. Save the place to keep it.`);
        });
        li.append(button);
        results.append(li);
      });
    } catch (e) {
      state.textContent = e.message || "Address search isn't reachable right now. Try again, or choose on the map.";
    }
  }
  field.querySelector("[data-pin-search]").addEventListener("click", search);
  query.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault(); // search, don't submit the place form
      search();
    }
  });

  // Show an existing pin as the draft when editing
  if (lat.value && lng.value && !selectedMarker) {
    setPin(parseFloat(lat.value), parseFloat(lng.value), "Pinned on the map.");
  }
})();
