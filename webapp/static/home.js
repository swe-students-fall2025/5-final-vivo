const sidebarTitle = document.getElementById("bathroom-title");
const sidebarAddress = document.getElementById("bathroom-address");
const addImageBtn = document.getElementById("add-image-btn");
const imageInput = document.getElementById("image-input");
const commentsList = document.getElementById("comments-list");
const commentInput = document.getElementById("comment-input");
const addCommentBtn = document.getElementById("add-comment-btn");
const directionsList = document.getElementById("directions-list");
const directionsSummary = document.getElementById("directions-summary");
const favoriteBtn = document.getElementById("favorite-btn");

let currentBathroomId = null;
let userFavorites = new Set();

async function fetchFavorites() {
  try {
    const res = await fetch("/api/users/favorites");
    if (res.ok) {
      const data = await res.json();
      userFavorites = new Set(data.favorites);
    }
  } catch (err) {
    console.error("Failed to fetch favorites:", err);
  }
}

function updateFavoriteButton(osm_id) {
  if (!favoriteBtn) return;
  if (userFavorites.has(osm_id)) {
    favoriteBtn.classList.remove("text-gray-400");
    favoriteBtn.classList.add("text-red-500");
  } else {
    favoriteBtn.classList.add("text-gray-400");
    favoriteBtn.classList.remove("text-red-500");
  }
}

if (favoriteBtn) {
  favoriteBtn.addEventListener("click", async (e) => {
    e.stopPropagation(); // Prevent bubbling if needed
    if (!currentBathroomId) return;

    const isFav = userFavorites.has(currentBathroomId);
    const method = isFav ? "DELETE" : "POST";

    try {
      const res = await fetch(`/api/users/favorites/${currentBathroomId}`, {
        method,
      });
      if (res.ok) {
        if (isFav) {
          userFavorites.delete(currentBathroomId);
        } else {
          userFavorites.add(currentBathroomId);
        }
        updateFavoriteButton(currentBathroomId);
      } else {
        console.error("Failed to toggle favorite");
      }
    } catch (err) {
      console.error("Error toggling favorite:", err);
    }
  });
}

// Call fetchFavorites on load
fetchFavorites();

function renderComments(reviews = []) {
  if (!commentsList) return;
  commentsList.innerHTML = "";

  reviews.forEach((r) => {
    const li = document.createElement("li");
    li.className = "p-2 bg-gray-100 rounded shadow-sm";
    li.innerHTML = `
            <div class="flex justify-between items-center">
                <span class="font-semibold text-sm">${r.user_name}</span>
                <span class="text-yellow-500">${"★".repeat(
                  Math.round(r.rating),
                )}${"☆".repeat(5 - Math.round(r.rating))}</span>
            </div>
            <p class="text-xs mt-1">${r.comment}</p>
        `;
    commentsList.appendChild(li);
  });
}

// fetch details for bathroom (reviews + images)
async function loadBathroomDetails(osm_id) {
  updateFavoriteButton(osm_id);
  try {
    const res = await fetch(`/api/bathrooms/${osm_id}`);
    const data = await res.json();

    // 1. Handle Reviews
    if (data.reviews) {
      renderComments(data.reviews);

      // use the average
      const avg =
        data.average_rating ??
        data.reviews.reduce((sum, r) => sum + r.rating, 0) /
          (data.reviews.length || 1);
      const count = data.rating_count ?? data.reviews.length;

      renderAverageRating(avg, count);
      const userEmail = window.currentUserEmail;
      const myReview = data.reviews.find((r) => r.user_email === userEmail);
      if (myReview) {
        selectedRating = myReview.rating;
        highlightStars(selectedRating);
        commentInput.value = myReview.comment;
      } else {
        selectedRating = null;
        highlightStars(0);
        commentInput.value = "";
      }
    } else {
      renderAverageRating(0, 0);
    }

    // 2. Handle Images
    const imageUrls = [];
    const tags = data.tags || {};
    if (tags.image) imageUrls.push(tags.image);
    if (tags.images && Array.isArray(tags.images))
      imageUrls.push(...tags.images);
    if (data.images && Array.isArray(data.images)) {
      imageUrls.push(...data.images);
    }
    showBathroomImages(imageUrls);
  } catch (err) {
    console.error("Failed to load details:", err);
  }
}

function renderAverageRating(avg = 0, count = 0) {
  const starsContainer = document.getElementById("average-stars");
  const countSpan = document.getElementById("rating-count");
  const numberSpan = document.getElementById("average-number");
  if (!starsContainer || !countSpan || !numberSpan) return;

  starsContainer.innerHTML = "";
  const fullStars = Math.floor(avg);
  const halfStar = avg - fullStars >= 0.5 ? 1 : 0;

  for (let i = 1; i <= 5; i++) {
    const star = document.createElement("span");
    if (i <= fullStars) star.textContent = "★";
    else if (i === fullStars + 1 && halfStar) star.textContent = "⯨";
    else star.textContent = "☆";
    starsContainer.appendChild(star);
  }

  numberSpan.textContent = avg > 0 ? avg.toFixed(1) : "";
  countSpan.textContent =
    count > 0 ? `(${count} review${count > 1 ? "s" : ""})` : "(No reviews yet)";
}

// post comments
addCommentBtn.addEventListener("click", async () => {
  const commentText = commentInput.value.trim();
  if (!commentText || !currentBathroomId) return;
  if (!selectedRating) {
    alert("Please select a rating!");
    return;
  }

  try {
    const res = await fetch(`/api/bathrooms/${currentBathroomId}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment: commentText, rating: selectedRating }),
    });

    if (!res.ok) {
      const errData = await res.json();
      alert(`Error: ${errData.error}`);
      return;
    }

    const updatedBathroom = await res.json();
    renderComments(updatedBathroom.reviews);
    renderAverageRating(
      updatedBathroom.average_rating || 0,
      updatedBathroom.rating_count || updatedBathroom.reviews.length,
    );

    const myReview = updatedBathroom.reviews.find(
      (r) => r.user_email === window.currentUserEmail,
    );
    if (myReview) {
      selectedRating = myReview.rating;
      highlightStars(selectedRating);
      commentInput.value = myReview.comment;
    } else {
      selectedRating = null;
      highlightStars(0);
      commentInput.value = "";
    }
  } catch (err) {
    console.error("Failed to post review:", err);
  }
});

// format address nicely from Overpass tags
function formatAddress(tags = {}, lat, lon) {
  const lines = [];

  if (tags.name) {
    lines.push(tags.name);
  }

  const street = [];
  if (tags["addr:housenumber"]) street.push(tags["addr:housenumber"]);
  if (tags["addr:street"]) street.push(tags["addr:street"]);
  if (street.length) lines.push(street.join(" "));

  const city = [];
  if (tags["addr:city"]) city.push(tags["addr:city"]);
  if (tags["addr:state"]) city.push(tags["addr:state"]);
  if (tags["addr:postcode"]) city.push(tags["addr:postcode"]);
  if (city.length) lines.push(city.join(", "));

  if (!lines.length) {
    lines.push(`Lat: ${lat.toFixed(6)}, Lon: ${lon.toFixed(6)}`);
  }

  return lines.join("<br>");
}

// sidebar
const map = L.map("map").setView([40.7128, -74.006], 13);
const sidebar = L.control
  .sidebar({
    container: "sidebar",
    position: "right",
    autopan: true,
    closeButton: true,
  })
  .addTo(map);

let bathroomSwiper = new Swiper(".bathroom-swiper", {
  loop: true,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  pagination: { el: ".swiper-pagination", clickable: true },
});

function showBathroomImages(imageUrls) {
  const swiperWrapper = document.querySelector(
    ".bathroom-swiper .swiper-wrapper",
  );
  swiperWrapper.innerHTML = "";

  const images = imageUrls?.length ? imageUrls : ["/static/img/default.png"];
  images.forEach((url) => {
    const slide = document.createElement("div");
    slide.classList.add("swiper-slide");

    const img = document.createElement("img");
    img.src = url;
    img.style.width = "100%";
    img.style.height = "auto";
    img.style.borderRadius = "8px";

    slide.appendChild(img);
    swiperWrapper.appendChild(slide);
  });

  bathroomSwiper.update();
}
if (addImageBtn && imageInput) {
  addImageBtn.addEventListener("click", () => imageInput.click());

  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      const img = new Image();
      img.onload = async function () {
        const maxWidth = 600;
        const maxHeight = 400;
        let width = img.width;
        let height = img.height;
        if (width > maxWidth) {
          height = (maxWidth / width) * height;
          width = maxWidth;
        }
        if (height > maxHeight) {
          width = (maxHeight / height) * width;
          height = maxHeight;
        }

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        const resizedUrl = canvas.toDataURL("image/png");

        if (!currentBathroomId) {
          alert("No bathroom selected!");
          return;
        }

        try {
          const res = await fetch(
            `/api/bathrooms/${currentBathroomId}/images`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ image: resizedUrl }),
            },
          );

          if (!res.ok) {
            const errData = await res.json();
            alert(`Error uploading image: ${errData.error}`);
            return;
          }

          // add
          const swiperWrapper = document.querySelector(
            ".bathroom-swiper .swiper-wrapper",
          );

          // remove default
          if (
            swiperWrapper.children.length === 1 &&
            swiperWrapper.children[0]
              .querySelector("img")
              .src.includes("default.png")
          ) {
            swiperWrapper.innerHTML = "";
          }

          const slide = document.createElement("div");
          slide.classList.add("swiper-slide");

          const newImg = document.createElement("img");
          newImg.src = resizedUrl;
          newImg.style.width = "100%";
          newImg.style.height = "auto";
          newImg.style.borderRadius = "8px";

          slide.appendChild(newImg);
          swiperWrapper.appendChild(slide);

          bathroomSwiper.update();
          bathroomSwiper.slideTo(swiperWrapper.children.length - 1);
        } catch (err) {
          console.error("Failed to upload image:", err);
          alert("Failed to upload image.");
        }
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// show routing
let userLatLng = null;
let routingControl = null;
map.locate({ setView: true, maxZoom: 16 });

map.on("locationfound", function (e) {
  userLatLng = e.latlng;

  L.circleMarker(userLatLng, {
    radius: 6,
    color: "blue",
    fillColor: "blue",
    fillOpacity: 1,
  }).addTo(map);
});

function routeTo(lat, lon) {
  if (!userLatLng) {
    // default loc, Courant
    userLatLng = { lat: 40.72869228853606, lng: -73.99555373403535 };
    // alert("User location not found yet!");
  }

  // remove previous route if exists
  if (routingControl) {
    map.removeControl(routingControl);
  }

  routingControl = L.Routing.control({
    waypoints: [L.latLng(userLatLng.lat, userLatLng.lng), L.latLng(lat, lon)],
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.8, weight: 5 }],
    },
    addWaypoints: false,
    draggableWaypoints: false,
    routeWhileDragging: false,
    show: false,
    createMarker: () => null,
    router: L.Routing.osrmv1({
      serviceUrl: "https://router.project-osrm.org/route/v1",
    }),
  })
    .on("routesfound", function (e) {
      const route = e.routes[0];

      // show summary
      const distanceKm = (route.summary.totalDistance / 1000).toFixed(1);
      const durationMin = Math.round(route.summary.totalTime / 60);
      directionsSummary.textContent = `Distance: ${distanceKm} km, Estimated time: ${durationMin} min`;

      // instruction
      if (directionsList) {
        directionsList.innerHTML = "";
        route.instructions.forEach((instr) => {
          const li = document.createElement("li");
          li.innerHTML = instr.text;
          directionsList.appendChild(li);
        });
      }
    })
    .addTo(map);
}

// search bar filter nyc
const nycViewbox = "-74.2591,40.9176,-73.7004,40.4774";

L.Control.geocoder({
  defaultMarkGeocode: false,
  placeholder: "Search NYC...",
  geocoder: L.Control.Geocoder.nominatim({
    geocodingQueryParams: {
      viewbox: nycViewbox,
      bounded: 1,
    },
  }),
})
  .on("markgeocode", function (e) {
    const center = e.geocode.center;
    map.setView(center, 19);
  })
  .addTo(map)
  .setPosition("topleft");

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// chikawa shark cluster
const markersLayer = L.markerClusterGroup({
  iconCreateFunction: function (cluster) {
    const count = cluster.getChildCount();
    const container = document.createElement("div");
    container.style.position = "relative";
    container.style.display = "inline-block";
    container.style.textAlign = "center";

    // add img
    const img = document.createElement("img");
    img.src = "/static/img/cluster.png";
    img.style.width = "50px";
    img.style.height = "50px";
    container.appendChild(img);

    // count
    const span = document.createElement("span");
    span.textContent = count;
    span.style.position = "absolute";
    span.style.bottom = "-5px";
    span.style.left = "50%";
    span.style.transform = "translateX(-50%)";
    span.style.fontWeight = "bold";
    span.style.color = "#161b29ff";
    span.style.fontFamily = "sans-serif";
    span.style.fontSize = "14px";
    container.appendChild(span);

    return L.divIcon({
      html: container.outerHTML,
      className: "",
    });
  },
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

// review star
const stars = document.querySelectorAll("#star-rating .star");
let selectedRating = null;

stars.forEach((star) => {
  const val = parseInt(star.dataset.value);

  star.addEventListener("mouseover", () => highlightStars(val));
  star.addEventListener("mouseout", () => highlightStars(selectedRating));
  star.addEventListener("click", () => {
    selectedRating = val;
    highlightStars(selectedRating);
  });
});

function highlightStars(rating) {
  stars.forEach((star) => {
    const val = parseInt(star.dataset.value);
    star.textContent = val <= rating ? "★" : "☆";
  });
}

// own location
function onLocationFound(e) {
  const latlng = e.latlng;

  L.circleMarker(latlng, {
    radius: 6,
    color: "red",
    fillColor: "red",
    fillOpacity: 1,
  }).addTo(map);
}

function onLocationError(e) {
  console.warn("Geolocation error:", e.message);
}

map.on("locationfound", onLocationFound);
map.on("locationerror", onLocationError);

function onLocationError(e) {
  console.warn("Geolocation error:", e.message);
}

map.on("locationfound", onLocationFound);
map.on("locationerror", onLocationError);

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
    .then((res) => res.json())
    .then((data) => {
      markersLayer.clearLayers();

      data.bathrooms.forEach((el) => {
        const lat = el.lat;
        const lon = el.lon;
        if (!lat || !lon) return;

        const marker = L.marker([lat, lon], { icon: toiletIcon });
        const tags = el.tags || {};
        const id = el.osm_id;

        marker.on("click", async () => {
          currentBathroomId = parseInt(id);
          if (sidebarTitle)
            sidebarTitle.textContent = tags.name || "Public Bathroom";

          if (sidebarAddress) {
            const hasAddressTags =
              tags["addr:housenumber"] ||
              tags["addr:street"] ||
              tags["addr:city"];
            if (hasAddressTags) {
              sidebarAddress.innerHTML = formatAddress(tags, lat, lon);
            } else {
              sidebarAddress.innerHTML = "Loading address...";
              const address = await reverseGeocode(lat, lon);
              sidebarAddress.innerHTML = address;
            }
          }

          loadBathroomDetails(id);
          sidebar.open("info");
          routeTo(lat, lon);
        });

        markersLayer.addLayer(marker);
      });
    })
    .catch((err) =>
      console.error("Error fetching bathrooms from MongoDB API:", err),
    );
}

fetchBathrooms();
