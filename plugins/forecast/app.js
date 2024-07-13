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
        const headers = {
            "User-Agent": "(myweatherapp.com, contact@myweatherapp.com)",
            "Accept": "application/geo+json"
        };

        // First, get the forecast URL for the location
        const pointsResponse = await fetch(`https://api.weather.gov/points/${lat},${lon}`, { headers });
        if (!pointsResponse.ok) {
            throw new Error(`HTTP error! status: ${pointsResponse.status}`);
        }
        const pointsData = await pointsResponse.json();

        // Now, get the actual forecast
        const forecastResponse = await fetch(pointsData.properties.forecast, { headers });
        if (!forecastResponse.ok) {
            throw new Error(`HTTP error! status: ${forecastResponse.status}`);
        }
        const forecastData = await forecastResponse.json();

        // Extract relevant information
        const currentPeriod = forecastData.properties.periods[0];
        const temperature = currentPeriod.temperature;
        const temperatureUnit = currentPeriod.temperatureUnit;
        const description = currentPeriod.shortForecast;
        const windSpeed = currentPeriod.windSpeed;
        const windDirection = currentPeriod.windDirection;
        const location = pointsData.properties.relativeLocation.properties.city + ', ' + 
                         pointsData.properties.relativeLocation.properties.state;
        
        const weatherInfo = document.getElementById('weather-info');
        weatherInfo.innerHTML = `
            <div class="weather-item"><i class="fas fa-map-marker-alt"></i> ${location}</div>
            <div class="weather-item"><i class="fas fa-cloud"></i> ${description}</div>
            <div class="weather-item"><i class="fas fa-thermometer-half"></i> ${temperature}°${temperatureUnit}</div>
            <div class="weather-item"><i class="fas fa-wind"></i> ${windSpeed} from ${windDirection}</div>
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