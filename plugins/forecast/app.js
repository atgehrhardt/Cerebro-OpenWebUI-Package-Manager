async function getLocationAndWeather() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(async function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            await getWeather(lat, lon);
        }, function(error) {
            console.error("Error getting location:", error);
            document.getElementById('weather-info').textContent = 'Error getting location. Please enable location services.';
        });
    } else {
        document.getElementById('weather-info').textContent = 'Geolocation is not supported by your browser.';
    }
}

async function getWeather(lat, lon) {
    try {
        const response = await fetch(`https://wttr.in/${lat},${lon}?format=%C+%t+%w+%p+%l`);
        const data = await response.text();
        const [condition, temperature, wind, precipitation, location] = data.split(' ');
        
        const weatherInfo = document.getElementById('weather-info');
        weatherInfo.innerHTML = `
            <div class="weather-item"><i class="fas fa-map-marker-alt"></i> ${location.replace('+', ' ')}</div>
            <div class="weather-item"><i class="fas fa-cloud"></i> ${condition}</div>
            <div class="weather-item"><i class="fas fa-thermometer-half"></i> ${temperature}</div>
            <div class="weather-item"><i class="fas fa-wind"></i> ${wind}</div>
            <div class="weather-item"><i class="fas fa-tint"></i> ${precipitation}</div>
        `;
    } catch (error) {
        console.error('Error fetching weather data:', error);
        document.getElementById('weather-info').textContent = 'Error fetching weather data';
    }
}

getLocationAndWeather();

function consumeEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    console.log('Key captured: ' + event.key);
}

window.addEventListener('keydown', consumeEvent, true);
window.addEventListener('keyup', consumeEvent, true);