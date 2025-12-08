const sidebarTitle   = document.getElementById('bathroom-title');
const sidebarAddress = document.getElementById('bathroom-address');
const bathroomImage  = document.getElementById('bathroom-image');
const addImageBtn    = document.getElementById('add-image-btn');
const imageInput     = document.getElementById('image-input');
const commentsList   = document.getElementById('comments-list');
const commentInput   = document.getElementById('comment-input');
const addCommentBtn  = document.getElementById('add-comment-btn');

let currentBathroomId = null;
const commentsByBathroomId = {}; 

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

// sidebar
const map = L.map('map').setView([40.7128, -74.0060], 13);
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

// chikawa shark cluster
const markersLayer = L.markerClusterGroup({
    iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        const container = document.createElement('div');
        container.style.position = 'relative';
        container.style.display = 'inline-block';
        container.style.textAlign = 'center';

        // add img
        const img = document.createElement('img');
        img.src = '/static/img/cluster.png';
        img.style.width = '50px';
        img.style.height = '50px';
        container.appendChild(img);

        // count
        const span = document.createElement('span');
        span.textContent = count;
        span.style.position = 'absolute';
        span.style.bottom = '-5px';
        span.style.left = '50%';
        span.style.transform = 'translateX(-50%)';
        span.style.fontWeight = 'bold';
        span.style.color = '#161b29ff';
        span.style.fontFamily = 'sans-serif';
        span.style.fontSize = '14px';
        container.appendChild(span);

        return L.divIcon({
            html: container.outerHTML,
            className: ""
        });
    }
});

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


// chikawa toilet marker
const toiletIcon = L.icon({
    iconUrl: "/static/img/toilet.png",  
    iconSize: [32, 32],    
    iconAnchor: [16, 32],  
});

// fetch the address from lat/lon
async function reverseGeocode(lat, lon) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.display_name) {
            return data.display_name;
        } else {
            return `Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`;
        }
    } catch (err) {
        console.error("Reverse geocoding error:", err);
        return `Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`;
    }
}

// Fetch bathrooms
function fetchBathrooms() {
    fetch("/api/bathrooms")
        .then(res => res.json())
        .then(data => {
            markersLayer.clearLayers();

            data.bathrooms.forEach(el => {
                const lat = el.lat;
                const lon = el.lon;
                if (!lat || !lon) return;

                const marker = L.marker([lat, lon], { icon: toiletIcon });
                const tags = el.tags || {};
                const id = el.osm_id; 

                marker.on('click', async () => {
                    currentBathroomId = id;
                    if (sidebarTitle) {
                        sidebarTitle.textContent = tags.name || 'Public Bathroom';
                    }
                    if (sidebarAddress) {
                        // overpass else geocode
                        const hasAddressTags = tags['addr:housenumber'] || tags['addr:street'] || tags['addr:city'];
                        if (hasAddressTags) {
                            sidebarAddress.innerHTML = formatAddress(tags, lat, lon);
                        } else {
                            sidebarAddress.innerHTML = "Loading address...";
                            const address = await reverseGeocode(lat, lon);
                            sidebarAddress.innerHTML = address;
                        }
                    }
                    if (bathroomImage) {
                        bathroomImage.src = "https://via.placeholder.com/260x160?text=No+Image";
                    }
                    renderComments();
                    sidebar.open('info');
                });
                markersLayer.addLayer(marker);
            });
        })
        .catch(err => console.error("Error fetching bathrooms from MongoDB API:", err));
}

fetchBathrooms();