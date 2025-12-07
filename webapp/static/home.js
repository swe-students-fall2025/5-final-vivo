// ===== Sidebar logic (DOM refs) =====
const sidebarTitle   = document.getElementById('bathroom-title');
const sidebarAddress = document.getElementById('bathroom-address');
const bathroomImage  = document.getElementById('bathroom-image');
const addImageBtn    = document.getElementById('add-image-btn');
const imageInput     = document.getElementById('image-input');
const commentsList   = document.getElementById('comments-list');
const commentInput   = document.getElementById('comment-input');
const addCommentBtn  = document.getElementById('add-comment-btn');

let currentBathroomId = null;
const commentsByBathroomId = {}; // { id: [comment, ...] }

// image upload preview
if (addImageBtn && imageInput && bathroomImage) {
    addImageBtn.addEventListener('click', () => imageInput.click());

    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (!file) return;
        const url = URL.createObjectURL(file);
        bathroomImage.src = url;
    });
}

function renderComments() {
    if (!commentsList || !currentBathroomId) return;

    commentsList.innerHTML = '';
    const comments = commentsByBathroomId[currentBathroomId] || [];
    comments.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        commentsList.appendChild(li);
    });
}

if (addCommentBtn && commentInput) {
    addCommentBtn.addEventListener('click', () => {
        const text = commentInput.value.trim();
        if (!text || !currentBathroomId) return;

        if (!commentsByBathroomId[currentBathroomId]) {
            commentsByBathroomId[currentBathroomId] = [];
        }
        commentsByBathroomId[currentBathroomId].push(text);
        commentInput.value = '';
        renderComments();
    });
}

// format address nicely from Overpass tags
function formatAddress(tags = {}, lat, lon) {
    const lines = [];

    if (tags.name) {
        lines.push(tags.name);
    }

    const street = [];
    if (tags['addr:housenumber']) street.push(tags['addr:housenumber']);
    if (tags['addr:street'])      street.push(tags['addr:street']);
    if (street.length) lines.push(street.join(' '));

    const city = [];
    if (tags['addr:city'])     city.push(tags['addr:city']);
    if (tags['addr:state'])    city.push(tags['addr:state']);
    if (tags['addr:postcode']) city.push(tags['addr:postcode']);
    if (city.length) lines.push(city.join(', '));

    if (!lines.length) {
        lines.push(`Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`);
    }

    return lines.join('<br>');
}

// ===== Map + Leaflet Sidebar =====

const map = L.map('map').setView([40.7128, -74.0060], 13);

// init Leaflet Sidebar (connects to <div id="sidebar"> in index.html)
const sidebar = L.control.sidebar({
    container: 'sidebar',
    position: 'right',
    autopan: true,
    closeButton: true
}).addTo(map);

// search bar filter nyc
const nycViewbox = '-74.2591,40.9176,-73.7004,40.4774';

L.Control.geocoder({
    defaultMarkGeocode: false,
    placeholder: "Search NYC...",
    geocoder: L.Control.Geocoder.nominatim({
        geocodingQueryParams: {
            viewbox: nycViewbox,
            bounded: 1
        }
    })
})
.on('markgeocode', function (e) {
    const center = e.geocode.center;
    map.setView(center, 19);
})
.addTo(map)
.setPosition('topleft');

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

const markersLayer = L.markerClusterGroup();
map.addLayer(markersLayer);

const overpassUrl = "https://overpass-api.de/api/interpreter";
const query = `
    [out:json][timeout:25];
    area["name"="City of New York"]["boundary"="administrative"]["admin_level"="5"]->.nyc;
    (
      node["amenity"="toilets"](area.nyc);
      way["amenity"="toilets"](area.nyc);
      relation["amenity"="toilets"](area.nyc);
    );
    out center;
`;

// Fetch bathrooms
function fetchBathrooms() {
    fetch(overpassUrl, {
        method: "POST",
        body: query
    })
        .then(res => res.json())
        .then(data => {
            markersLayer.clearLayers();

            data.elements.forEach(el => {
                const lat = el.lat || (el.center && el.center.lat);
                const lon = el.lon || (el.center && el.center.lon);
                if (!lat || !lon) return;

                const marker = L.marker([lat, lon]);
                const tags = el.tags || {};
                const id = el.id;

                marker.on('click', () => {
                    currentBathroomId = id;

                    if (sidebarTitle) {
                        sidebarTitle.textContent = tags.name || 'Public Bathroom';
                    }
                    if (sidebarAddress) {
                        sidebarAddress.innerHTML = formatAddress(tags, lat, lon);
                    }

                    // reset image to default when switching bathrooms
                    if (bathroomImage) {
                        bathroomImage.src = "https://via.placeholder.com/260x160?text=No+Image";
                    }

                    renderComments();
                    sidebar.open('info');
                });

                markersLayer.addLayer(marker);
            });
        })
        .catch(err => console.error("Overpass API error:", err));
}

fetchBathrooms();