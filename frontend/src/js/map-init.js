import '/assets/js/layout.js'
import '/assets/js/api.js'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const COLORS = { high: '#EF4444', medium: '#F59E0B', low: '#0091EA' }
let map, markersLayer, allCountries = []
function getColor(sev) { return COLORS[sev] || '#6B7280' }

function initMap(center, zoom) {
  if (map) return
  map = L.map('map', { zoomControl: false, attributionControl: false }).setView(center || [20, 0], zoom || 2)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map)
  markersLayer = L.layerGroup().addTo(map)
}

function addMarker(lat, lng, label, count) {
  const color = getColor(count > 50 ? 'high' : count > 20 ? 'medium' : 'low')
  const icon = L.divIcon({
    className: '',
    html: '<div style="width:20px;height:20px;background:' + color + ';border:3px solid ' + color + 'cc;border-radius:50%;box-shadow:0 0 12px ' + color + '44;"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
  const m = L.marker([lat, lng], { icon }).addTo(markersLayer)
  m.bindPopup('<b>' + label + '</b><br/>' + count + ' article' + (count !== 1 ? 's' : ''), { className: 'map-popup' })
  m.on('click', function () { window.focusCountry(label) })
  return m
}

function renderSidebar(countries) {
  const sidebar = document.getElementById('countryList')
  const emoji = {
    US: '\u{1F1FA}\u{1F1F8}', UK: '\u{1F1EC}\u{1F1E7}', India: '\u{1F1EE}\u{1F1F3}',
    Germany: '\u{1F1E9}\u{1F1EA}', France: '\u{1F1EB}\u{1F1F7}', China: '\u{1F1E8}\u{1F1F3}',
    Russia: '\u{1F1F7}\u{1F1FA}', Japan: '\u{1F1EF}\u{1F1F5}', Brazil: '\u{1F1E7}\u{1F1F7}',
    Canada: '\u{1F1E8}\u{1F1E6}', Australia: '\u{1F1E6}\u{1F1FA}', Spain: '\u{1F1EA}\u{1F1F8}',
    Italy: '\u{1F1EE}\u{1F1F9}', Switzerland: '\u{1F1E8}\u{1F1ED}',
    Netherlands: '\u{1F1F3}\u{1F1F1}', Singapore: '\u{1F1F8}\u{1F1EC}',
    EU: '\u{1F1EA}\u{1F1FA}', 'South Africa': '\u{1F1FF}\u{1F1E6}',
    'South Korea': '\u{1F1F0}\u{1F1F7}', 'North Korea': '\u{1F1F0}\u{1F1F5}',
    UAE: '\u{1F1E6}\u{1F1EA}', 'Saudi Arabia': '\u{1F1F8}\u{1F1E6}',
    Israel: '\u{1F1EE}\u{1F1F1}', Iran: '\u{1F1EE}\u{1F1F7}',
    Turkey: '\u{1F1F9}\u{1F1F7}', Pakistan: '\u{1F1F5}\u{1F1F0}',
    Bangladesh: '\u{1F1E7}\u{1F1E9}', Nigeria: '\u{1F1F3}\u{1F1EC}',
    Kenya: '\u{1F1F0}\u{1F1EA}', Egypt: '\u{1F1EA}\u{1F1EC}',
    Argentina: '\u{1F1E6}\u{1F1F7}', Mexico: '\u{1F1F2}\u{1F1FD}',
    Colombia: '\u{1F1E8}\u{1F1F4}', Chile: '\u{1F1E8}\u{1F1F1}',
    Sweden: '\u{1F1F8}\u{1F1EA}', Norway: '\u{1F1F3}\u{1F1F4}',
    Denmark: '\u{1F1E9}\u{1F1F0}', Finland: '\u{1F1EB}\u{1F1EE}',
    Poland: '\u{1F1F5}\u{1F1F1}', Ukraine: '\u{1F1FA}\u{1F1E6}',
    'New Zealand': '\u{1F1F3}\u{1F1FF}', Indonesia: '\u{1F1EE}\u{1F1E9}',
    Vietnam: '\u{1F1FB}\u{1F1F3}', Thailand: '\u{1F1F9}\u{1F1ED}',
    Malaysia: '\u{1F1F2}\u{1F1FE}', Philippines: '\u{1F1F5}\u{1F1ED}',
    Taiwan: '\u{1F1F9}\u{1F1FC}', 'Hong Kong': '\u{1F1ED}\u{1F1F0}',
  }
  if (sidebar) {
    sidebar.innerHTML = countries.map(function (c) {
      return '<div class="card" data-country="' + c.country + '" onclick="window.focusCountry(\'' + c.country + '\')"><div class="flex items-center gap-3"><span style="font-size:20px">' + (emoji[c.country] || '\u{1F30D}') + '</span><div><div class="font-semibold text-sm">' + c.country + '</div><div class="text-xs text-muted">' + c.count + ' active events</div></div></div></div>'
    }).join('')
  }
}

window.focusCountry = async function (name) {
  const c = allCountries.find(function (x) { return x.country === name })
  if (!c) return
  document.querySelectorAll('#countryList .card').forEach(function (el) { el.classList.remove('active') })
  var card = document.querySelector('#countryList .card[data-country="' + name + '"]')
  if (card) card.classList.add('active')
  map.setView([c.lat, c.lng], 4, { animate: true })

  const drawer = document.getElementById('mapInspectorDrawer')
  const drawerTitle = document.getElementById('drawerCountryTitle')
  const drawerBody = document.getElementById('drawerBody')
  if (drawer && drawerBody) {
    if (drawerTitle) drawerTitle.textContent = `${c.country} Intelligence`
    drawerBody.innerHTML = '<div class="p-4 text-center text-muted">Loading country data...</div>'
    drawer.classList.add('open')

    let articlesHtml = ''
    try {
      const res = await fetch(`/api/news/geo/${encodeURIComponent(name)}/articles?limit=10`)
      if (res.ok) {
        const data = await res.json()
        if (data.articles && data.articles.length) {
          articlesHtml = data.articles.map(a =>
            `<div style="padding:10px 0;border-bottom:1px solid var(--border)">
              <a href="article.html?id=${a.id}" class="font-semibold text-sm line-clamp-2" style="color:var(--text-primary);text-decoration:none">${a.title}</a>
              <div class="text-xs text-muted mt-1">${a.source?.name || 'News'} · ${timeAgo(a.published_at)}</div>
            </div>`
          ).join('')
        }
      }
    } catch (_) {}

    if (!articlesHtml) {
      articlesHtml = '<div class="text-xs text-muted p-2">No recent articles found for this country.</div>'
    }

    const keywordsHtml = (c.top_keywords || ['news', 'market', 'policy']).map(k =>
      `<span style="font-size:10px;padding:2px 8px;border-radius:12px;background:var(--bg-elevated);color:var(--accent);margin-right:4px">${k}</span>`
    ).join('')

    drawerBody.innerHTML = `
      <div class="card p-4 mb-4">
        <div class="text-xs text-muted mb-1">Total Events</div>
        <div class="font-bold text-lg text-accent">${c.count} Active News Stories</div>
        <div class="mt-3 text-xs text-muted mb-1">Top Keywords</div>
        <div>${keywordsHtml}</div>
      </div>
      <h4 class="font-semibold text-sm mb-3">Latest Stories</h4>
      <div>${articlesHtml}</div>
    `
  }
}

;(async function loadMap() {
  let countries = []
  try {
    const resp = await fetch('/api/news/geo')
    const data = await resp.json()
    countries = data.countries || []
  } catch (_) {}
  if (!countries.length) {
    countries = [
      { country: 'US', count: 128, lat: 37.09, lng: -95.71, severity: 'high' },
      { country: 'UK', count: 87, lat: 55.38, lng: -3.44, severity: 'high' },
      { country: 'India', count: 64, lat: 20.59, lng: 78.96, severity: 'high' },
      { country: 'Germany', count: 42, lat: 51.17, lng: 10.45, severity: 'medium' },
      { country: 'France', count: 38, lat: 46.60, lng: 1.89, severity: 'medium' },
      { country: 'China', count: 56, lat: 35.86, lng: 104.20, severity: 'high' },
      { country: 'Russia', count: 45, lat: 61.52, lng: 105.32, severity: 'medium' },
      { country: 'Japan', count: 29, lat: 36.20, lng: 138.25, severity: 'medium' },
      { country: 'Brazil', count: 22, lat: -14.24, lng: -51.93, severity: 'medium' },
      { country: 'Canada', count: 18, lat: 56.13, lng: -106.35, severity: 'low' },
      { country: 'Australia', count: 15, lat: -25.27, lng: 133.78, severity: 'low' },
      { country: 'Spain', count: 12, lat: 40.46, lng: -3.75, severity: 'low' },
      { country: 'Italy', count: 14, lat: 41.87, lng: 12.57, severity: 'low' },
      { country: 'Switzerland', count: 8, lat: 46.82, lng: 8.23, severity: 'low' },
      { country: 'Netherlands', count: 6, lat: 52.13, lng: 5.29, severity: 'low' },
      { country: 'Singapore', count: 11, lat: 1.35, lng: 103.82, severity: 'low' },
      { country: 'South Africa', count: 9, lat: -30.56, lng: 22.94, severity: 'low' },
    ]
  }
  allCountries = countries
  const total = countries.reduce(function (s, c) { return s + c.count }, 0)
  var headerP = document.querySelector('.section-header p')
  if (headerP) headerP.textContent = total + ' active events across ' + countries.length + ' countries'
  initMap([20, 0], 2)
  for (const c of countries) {
    addMarker(c.lat, c.lng, c.country, c.count)
  }
  renderSidebar(countries)
})()
