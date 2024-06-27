const RSS_URL = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en";
const API_URL = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
  RSS_URL
)}`;

function fetchNews() {
  const newsListElement = document.getElementById("news-list");
  newsListElement.innerHTML = '<div id="loading">Fetching news...</div>';

  fetch(API_URL)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.status !== "ok") {
        throw new Error("Error fetching RSS feed");
      }
      if (data.items.length === 0) {
        throw new Error("No news items found in the feed");
      }
      let html = '<div class="news-grid">';
      data.items.forEach((item) => {
        html += `
                            <div class="news-item">
                                <a href="${item.link}" target="_blank">
                                    ${item.title}
                                </a>
                            </div>
                        `;
      });
      html += "</div>";
      newsListElement.innerHTML = html;
    })
    .catch((error) => {
      console.error("Error fetching news:", error);
      newsListElement.innerHTML = `<p>Error loading news: ${error.message}. Please try again later.</p>
                                                 <p>Technical details: ${error.stack}</p>`;
    });
}

fetchNews();
setInterval(fetchNews, 300000); // Refresh every 5 minutes
function consumeEvent(event) {
  event.preventDefault();
  event.stopPropagation();
  console.log("Key captured: " + event.key);
}

window.addEventListener("keydown", consumeEvent, true);
window.addEventListener("keyup", consumeEvent, true);
