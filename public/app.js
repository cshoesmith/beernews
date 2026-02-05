const API_BASE = '/api';

let userLocation = null;
let currentTab = 'recommendations';

// Trending data cache
let trendingData = { beers: [], venues: [], styles: [] };
let currentTrendingTab = 'beers';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setCurrentDate();
    loadStats();
    loadSuburbs();
    loadTrending();
    loadRecommendations();
    loadNewReleases();
    loadVenues();
    
    // Section navigation (tabs)
    document.querySelectorAll('.section-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = link.dataset.tab;
            if (tabName) {
                switchTab(tabName);
                
                // Update active state
                document.querySelectorAll('.section-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            }
        });
    });
    
    // Filter changes
    document.getElementById('suburb-filter').addEventListener('change', () => {
        refreshAll();
    });
    
    document.getElementById('style-filter').addEventListener('change', () => {
        refreshAll();
    });
    
    // Location button
    document.getElementById('location-toggle').addEventListener('click', getUserLocation);
    
    // Metrics toggle button
    document.getElementById('metrics-toggle').addEventListener('click', toggleMetrics);
    
    // Trending tabs
    document.querySelectorAll('.trending-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            currentTrendingTab = tab.dataset.tab;
            renderTrending();
            
            // Update active state
            document.querySelectorAll('.trending-tab').forEach(t => {
                t.style.background = t.dataset.tab === currentTrendingTab ? '#f0f0f0' : 'transparent';
                t.classList.toggle('active', t.dataset.tab === currentTrendingTab);
            });
        });
    });
});

function setCurrentDate() {
    const now = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    const dateStr = now.toLocaleDateString('en-AU', options);
    document.getElementById('current-date').textContent = dateStr;
    document.getElementById('hero-timestamp').textContent = dateStr;
}

function switchTab(tabName) {
    currentTab = tabName;
    
    // Hide all content sections
    document.querySelectorAll('.main-article').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Show selected content
    document.getElementById(`content-${tabName}`).classList.remove('hidden');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function refreshAll() {
    loadRecommendations();
    loadNewReleases();
    loadVenues();
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        document.getElementById('stat-venues').textContent = stats.total_venues;
        document.getElementById('stat-new').textContent = stats.new_releases_7d;
        document.getElementById('stat-breweries').textContent = stats.breweries;
        document.getElementById('stat-bars').textContent = stats.bars;
        
        // Update breaking news with latest info
        if (stats.new_releases_7d > 0) {
            document.getElementById('breaking-news').textContent = 
                `${stats.new_releases_7d} new beer releases found this week across ${stats.venues_with_new_releases} venues`;
        }
        
        // Show last updated time
        if (stats.last_updated) {
            const updateTime = new Date(stats.last_updated);
            const now = new Date();
            const diffMs = now - updateTime;
            const hoursAgo = Math.floor(diffMs / (1000 * 60 * 60));
            const daysAgo = Math.floor(hoursAgo / 24);
            
            let timeText;
            if (hoursAgo < 1) {
                const minsAgo = Math.floor(diffMs / (1000 * 60));
                timeText = minsAgo < 1 ? 'Just now' : `${minsAgo}m ago`;
            } else if (hoursAgo < 24) {
                timeText = `${hoursAgo}h ago`;
            } else {
                timeText = `${daysAgo}d ago`;
            }
            
            document.getElementById('last-updated').textContent = `Updated ${timeText}`;
        }
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

async function loadSuburbs() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        const select = document.getElementById('suburb-filter');
        select.innerHTML = '<option value="">All Suburbs</option>';
        
        const suburbs = stats.popular_suburbs.sort();
        suburbs.forEach(suburb => {
            const option = document.createElement('option');
            option.value = suburb;
            option.textContent = suburb;
            select.appendChild(option);
        });
        
        // Update suburb list in right rail
        const suburbList = document.getElementById('suburb-list');
        if (suburbList) {
            suburbList.innerHTML = suburbs.slice(0, 8).map(suburb => 
                `<li><a href="#" onclick="filterBySuburb('${suburb}'); return false;">${suburb}</a></li>`
            ).join('');
        }
    } catch (err) {
        console.error('Failed to load suburbs:', err);
    }
}

function filterBySuburb(suburb) {
    document.getElementById('suburb-filter').value = suburb;
    refreshAll();
}

async function loadTrending() {
    try {
        const response = await fetch(`${API_BASE}/trending`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Trending API error:', data.error);
            document.getElementById('trending-list').innerHTML = `<li style="color: #999;">Error: ${data.error}</li>`;
            return;
        }
        
        trendingData = {
            beers: data.beers || [],
            venues: data.venues || [],
            styles: data.styles || []
        };
        
        // If all arrays are empty, show a message but with the count
        const totalItems = trendingData.beers.length + trendingData.venues.length + trendingData.styles.length;
        if (totalItems === 0) {
            document.getElementById('trending-list').innerHTML = `<li style="color: #999; font-style: italic;">No trending data yet (${data.total_checkins || 0} checkins tracked)</li>`;
            return;
        }
        
        renderTrending();
    } catch (err) {
        console.error('Failed to load trending:', err);
        document.getElementById('trending-list').innerHTML = '<li style="color: #999;">Unable to load trending data</li>';
    }
}

function renderTrending() {
    const list = document.getElementById('trending-list');
    
    if (!trendingData || !trendingData[currentTrendingTab]) {
        list.innerHTML = '<li style="color: #999; font-style: italic;">Loading...</li>';
        return;
    }
    
    const items = trendingData[currentTrendingTab] || [];
    
    if (items.length === 0) {
        // Show a friendly message with suggestions
        const suggestions = {
            beers: 'Check back after more venue checkins',
            venues: 'Visit venues to see activity',
            styles: 'Styles will appear with more data'
        };
        list.innerHTML = `<li style="color: #999; font-style: italic; padding: 8px 0;">${suggestions[currentTrendingTab] || 'No data yet'}</li>`;
        return;
    }
    
    list.innerHTML = items.map((item, index) => {
        const safeName = item.name ? item.name.replace(/'/g, "\\'") : 'Unknown';
        const clickHandler = item.type === 'venue' 
            ? `onclick="filterBySuburb('${safeName}'); return false;"`
            : item.type === 'style'
            ? `onclick="filterByStyle('${safeName}'); return false;"`
            : `onclick="searchBeer('${safeName}'); return false;"`;
        
        return `<li>
            <a href="#" ${clickHandler} style="display: flex; justify-content: space-between; align-items: baseline;">
                <span>${item.name || 'Unknown'}</span>
                <span style="font-size: 0.75rem; color: #999; font-weight: 500;">${item.count || 0} checkins</span>
            </a>
        </li>`;
    }).join('');
}

function filterByStyle(style) {
    document.getElementById('style-filter').value = style;
    refreshAll();
}

function searchBeer(beerName) {
    // Switch to new releases tab and filter
    switchTab('new-releases');
    document.querySelectorAll('.section-link').forEach(l => l.classList.remove('active'));
    document.querySelector('.section-link[data-tab="new-releases"]').classList.add('active');
    // The beer will be visible in the list if it's recent
}

async function loadRecommendations() {
    const container = document.getElementById('recommendations-list');
    
    container.innerHTML = '<div class="loading">Finding the best spots for you...</div>';
    
    try {
        const suburb = document.getElementById('suburb-filter').value;
        const style = document.getElementById('style-filter').value;
        
        let url = `${API_BASE}/recommendations?days=7`;
        if (suburb) url += `&suburb=${encodeURIComponent(suburb)}`;
        if (style) url += `&liked_styles=${encodeURIComponent(style)}`;
        if (userLocation) {
            url += `&user_lat=${userLocation.lat}&user_lng=${userLocation.lng}`;
        }
        
        const response = await fetch(url);
        const recommendations = await response.json();
        
        if (recommendations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🍺</div>
                    <h3>No recommendations found</h3>
                    <p>Try adjusting your filters or check back later for new releases!</p>
                </div>
            `;
            return;
        }
        
        // First recommendation is featured
        let html = '';
        recommendations.forEach((rec, index) => {
            const isFeatured = index === 0;
            html += createStoryCard(rec, isFeatured);
        });
        
        container.innerHTML = html;
        
    } catch (err) {
        container.innerHTML = `<div class="empty-state">Error loading recommendations: ${err.message}</div>`;
    }
}

function createStoryCard(rec, isFeatured = false) {
    const distanceText = rec.distance_km !== null 
        ? `<span class="distance">${rec.distance_km.toFixed(1)} km away</span>` 
        : '';
    
    const beerList = rec.new_beers.map(beer => {
        const releaseDate = new Date(beer.release_date);
        const now = new Date();
        const daysAgo = Math.floor((now - releaseDate) / (1000 * 60 * 60 * 24));
        const hoursAgo = Math.floor((now - releaseDate) / (1000 * 60 * 60));
        
        let timeText;
        if (hoursAgo < 1) {
            timeText = 'Just now';
        } else if (hoursAgo < 24) {
            timeText = `${hoursAgo}h ago`;
        } else if (daysAgo === 1) {
            timeText = 'Yesterday';
        } else {
            timeText = `${daysAgo} days ago`;
        }
        
        return `
        <div class="beer-item">
            <div class="beer-name">${beer.name} <span class="new-badge">New</span></div>
            <div class="beer-details">${beer.style} • ${beer.abv}% ABV</div>
            <div class="beer-time">Released: ${timeText}</div>
        </div>
    `}).join('');
    
    const posts = rec.relevant_posts.map(post => `
        <div class="post-content">"${post.content.substring(0, 150)}${post.content.length > 150 ? '...' : ''}"</div>
    `).join('');
    
    const featuredClass = isFeatured ? 'featured' : '';
    const kicker = isFeatured ? 'Top Pick' : rec.venue.type === 'brewery' ? 'Brewery' : 'Venue';
    
    return `
        <article class="story-card ${featuredClass}">
            <div class="story-content">
                <div class="story-kicker">${kicker}</div>
                <h3 class="story-headline">
                    <a href="#">${rec.venue.name}</a>
                </h3>
                <p class="story-summary">
                    ${rec.venue.address}, ${rec.venue.suburb}. ${rec.reason}
                </p>
                <div class="story-meta">
                    <span class="author">${rec.venue.type === 'brewery' ? 'Brewery' : 'Craft Beer Bar'}</span>
                    ${distanceText}
                </div>
                ${beerList ? `<div class="beer-list">${beerList}</div>` : ''}
                ${posts ? `
                    <div class="posts-section">
                        <div class="posts-title">Latest Update</div>
                        ${posts}
                    </div>
                ` : ''}
            </div>
        </article>
    `;
}

async function loadNewReleases() {
    const container = document.getElementById('beers-list');
    
    container.innerHTML = '<div class="loading">Loading new releases...</div>';
    
    try {
        const url = `${API_BASE}/beers/new?days=7`;
        const response = await fetch(url);
        const beers = await response.json();
        
        // Get venues for mapping
        const venuesResponse = await fetch(`${API_BASE}/venues`);
        const venues = await venuesResponse.json();
        const venueMap = {};
        venues.forEach(v => venueMap[v.id] = v);
        
        if (beers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🍺</div>
                    <h3>No new releases this week</h3>
                    <p>Check back soon for the latest drops!</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        beers.forEach(beer => {
            const brewery = venueMap[beer.brewery_id];
            const releaseDate = new Date(beer.release_date);
            const now = new Date();
            const daysAgo = Math.floor((now - releaseDate) / (1000 * 60 * 60 * 24));
            const hoursAgo = Math.floor((now - releaseDate) / (1000 * 60 * 60));
            
            let timeText;
            if (hoursAgo < 1) {
                timeText = 'Just now';
            } else if (hoursAgo < 24) {
                timeText = `${hoursAgo}h ago`;
            } else if (daysAgo === 1) {
                timeText = 'Yesterday';
            } else {
                timeText = `${daysAgo} days ago`;
            }
            
            html += `
                <div class="list-item">
                    <div class="item-date">${timeText}</div>
                    <div class="item-content">
                        <h4>${beer.name} <span class="new-badge">New Release</span></h4>
                        <p>${beer.description || `${beer.style} from ${brewery ? brewery.name : (beer.brewery_name || 'Unknown Brewery')}`}</p>
                        <div class="item-tags">
                            <span class="tag">${beer.style}</span>
                            <span class="tag">${beer.abv}% ABV</span>
                            ${brewery ? `<span class="tag">${brewery.suburb}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (err) {
        container.innerHTML = `<div class="empty-state">Error loading beers: ${err.message}</div>`;
    }
}

async function loadVenues() {
    const container = document.getElementById('venues-list');
    
    container.innerHTML = '<div class="loading">Loading venues...</div>';
    
    try {
        const suburb = document.getElementById('suburb-filter').value;
        
        let url = `${API_BASE}/venues`;
        if (suburb) url += `?suburb=${encodeURIComponent(suburb)}`;
        
        const response = await fetch(url);
        const venues = await response.json();
        
        if (venues.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📍</div>
                    <h3>No venues found</h3>
                    <p>Try a different suburb filter.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        venues.forEach(venue => {
            const distanceText = userLocation
                ? `<span class="distance">${calculateDistance(userLocation.lat, userLocation.lng, venue.location[0], venue.location[1]).toFixed(1)} km</span>`
                : '';
            
            html += `
                <div class="venue-card">
                    <div class="venue-type-label">${venue.type}</div>
                    <h4>${venue.name}</h4>
                    <div class="venue-address">${venue.address}</div>
                    <div class="venue-meta">
                        ${venue.suburb}
                        ${distanceText}
                    </div>
                    ${venue.instagram_handle ? `<div style="margin-top: 8px; font-size: 0.75rem; color: #999;">${venue.instagram_handle}</div>` : ''}
                </div>
            `;
        });
        
        container.innerHTML = html;
        
    } catch (err) {
        container.innerHTML = `<div class="empty-state">Error loading venues: ${err.message}</div>`;
    }
}

function getUserLocation() {
    const btn = document.getElementById('location-toggle');
    const status = document.getElementById('location-status');
    
    btn.textContent = 'Getting location...';
    btn.disabled = true;
    
    if (!navigator.geolocation) {
        status.textContent = 'Geolocation is not supported by your browser';
        status.classList.remove('hidden');
        btn.innerHTML = '<span class="location-icon">📍</span> Use My Location';
        btn.disabled = false;
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            
            btn.innerHTML = '<span class="location-icon">✓</span> Location Set';
            btn.disabled = false;
            
            status.innerHTML = `Using your location: ${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}`;
            status.classList.remove('hidden');
            
            loadRecommendations();
            loadVenues();
        },
        (err) => {
            status.textContent = `Could not get location: ${err.message}`;
            status.classList.remove('hidden');
            btn.innerHTML = '<span class="location-icon">📍</span> Use My Location';
            btn.disabled = false;
        }
    );
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function toggleMetrics() {
    const panel = document.getElementById('metrics-panel');
    const isHidden = panel.classList.contains('hidden');
    
    if (isHidden) {
        panel.classList.remove('hidden');
        loadMetrics();
    } else {
        panel.classList.add('hidden');
    }
}

async function loadMetrics() {
    const container = document.getElementById('metrics-content');
    container.innerHTML = 'Loading metrics...';
    
    try {
        const response = await fetch(`${API_BASE}/metrics`);
        const data = await response.json();
        
        if (data.error) {
            container.innerHTML = `<p>Metrics not available yet.</p>`;
            return;
        }
        
        let html = '';
        
        // Overall stats
        html += `
            <div style="margin-bottom: 20px; padding: 12px; background: #f0fdf4; border-left: 3px solid #2ea44f;">
                <div style="font-weight: 600; color: #2ea44f;">${data.overall?.success_rate || 0}% Success Rate</div>
                <div style="font-size: 0.8rem; color: #666;">
                    ${data.overall?.total_successes || 0} successes / ${data.overall?.total_attempts || 0} attempts
                </div>
            </div>
        `;
        
        // Individual sources - show all, sorted by items found (most productive first)
        if (data.sources && Object.keys(data.sources).length > 0) {
            const sortedSources = Object.entries(data.sources)
                .sort((a, b) => b[1].items_found - a[1].items_found);
            
            html += `<div style="max-height: 400px; overflow-y: auto; border: 1px solid var(--nyt-border); padding: 12px; margin-bottom: 16px;">`;
            
            for (const [sourceName, sourceData] of sortedSources) {
                const statusIcon = sourceData.status === 'active' ? '●' : sourceData.status === 'struggling' ? '▲' : '○';
                const statusColor = sourceData.status === 'active' ? '#2ea44f' : sourceData.status === 'struggling' ? '#f59e0b' : '#999';
                
                html += `
                    <div class="metric-source" style="padding: 10px 0; border-bottom: 1px dotted var(--nyt-border);">
                        <div class="metric-name" style="color: ${statusColor}; font-weight: 600;">${statusIcon} ${sourceName}</div>
                        <div class="metric-tech">${sourceData.technique} | ${sourceData.attempts || 0} attempts</div>
                        <div class="metric-stats" style="margin-top: 4px;">
                            <span class="metric-success" style="color: ${sourceData.success_rate >= 50 ? '#2ea44f' : '#f59e0b'}; font-weight: 600;">${sourceData.success_rate}% success</span>
                            <span class="metric-items" style="margin-left: 12px; color: var(--nyt-gray);">${sourceData.items_found} items found</span>
                        </div>
                        ${sourceData.note ? `<div style="font-size: 0.75rem; color: var(--nyt-light-gray); margin-top: 4px;">${sourceData.note}</div>` : ''}
                    </div>
                `;
            }
            
            html += `</div>`;
            html += `<p style="font-size: 0.8rem; color: var(--nyt-gray); text-align: center;">Showing ${sortedSources.length} data sources</p>`;
        } else {
            html += '<p style="font-size: 0.85rem; color: #666;">No metrics data yet.</p>';
        }
        
        container.innerHTML = html;
        
    } catch (err) {
        container.innerHTML = `<p style="font-size: 0.85rem; color: #666;">Error loading metrics.</p>`;
    }
}
