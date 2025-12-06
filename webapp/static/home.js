const map = L.map('map').setView([40.7128, -74.0060], 13); 
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
            if (lat && lon) {
                const marker = L.marker([lat, lon])
                markersLayer.addLayer(marker);
            }
        });
    })
    .catch(err => console.error("Overpass API error:", err));
}

fetchBathrooms();
