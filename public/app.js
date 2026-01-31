const API_BASE = '/api';

let userLocation = null;
let currentTab = 'recommendations';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadSuburbs();
    loadRecommendations();
    loadNewReleases();
    loadVenues();
    
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
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
});

function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`content-${tabName}`).classList.add('active');
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
        
        // Show last updated time
        if (stats.last_updated) {
            const updateTime = new Date(stats.last_updated);
            const now = new Date();
            const hoursAgo = Math.floor((now - updateTime) / (1000 * 60 * 60));
            const daysAgo = Math.floor(hoursAgo / 24);
            
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
            
            document.getElementById('last-updated').textContent = 
                `🔄 Data updated: ${timeText} (${updateTime.toLocaleDateString('en-AU', {hour: '2-digit', minute:'2-digit'})})`;
        }
    } catch (err) {
        console.error('Failed to load stats:', err);
        document.getElementById('last-updated').textContent = 'Unable to check last update';
    }
}

async function loadSuburbs() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const stats = await response.json();
        
        const select = document.getElementById('suburb-filter');
        // Keep the "All Suburbs" option
        select.innerHTML = '<option value="">All Suburbs</option>';
        
        const suburbs = stats.popular_suburbs.sort();
        suburbs.forEach(suburb => {
            const option = document.createElement('option');
            option.value = suburb;
            option.textContent = suburb;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to load suburbs:', err);
    }
}

async function loadRecommendations() {
    const loading = document.getElementById('rec-loading');
    const container = document.getElementById('recommendations-list');
    
    loading.style.display = 'block';
    container.innerHTML = '';
    
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
        
        loading.style.display = 'none';
        
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
        
        recommendations.forEach(rec => {
            container.appendChild(createRecommendationCard(rec));
        });
    } catch (err) {
        loading.style.display = 'none';
        container.innerHTML = `<p class="empty-state">Error loading recommendations: ${err.message}</p>`;
    }
}

function createRecommendationCard(rec) {
    const card = document.createElement('div');
    card.className = 'card';
    
    const distanceText = rec.distance_km !== null 
        ? `<span class="distance">📍 ${rec.distance_km.toFixed(1)} km away</span>` 
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
        
        const dateStr = releaseDate.toLocaleDateString('en-AU', {
            weekday: 'short',
            day: 'numeric',
            month: 'short'
        });
        
        return `
        <div class="beer-item">
            <div class="beer-info">
                <div class="beer-name">${beer.name}</div>
                <div class="beer-details">${beer.style} • ${beer.abv}% ABV</div>
                <div class="beer-time">📅 ${dateStr} • ${timeText}</div>
            </div>
            <span class="beer-badge">NEW</span>
        </div>
    `}).join('');
    
    const posts = rec.relevant_posts.map(post => `
        <div class="post-content">${post.content}</div>
    `).join('');
    
    card.innerHTML = `
        <div class="card-header">
            <div>
                <div class="venue-name">${rec.venue.name}</div>
                <span class="venue-type ${rec.venue.type}">${rec.venue.type}</span>
            </div>
        </div>
        <div class="venue-address">${rec.venue.address}</div>
        <div class="venue-meta">
            <span>📍 ${rec.venue.suburb}</span>
            ${distanceText}
        </div>
        <div class="reason">💡 ${rec.reason}</div>
        <div class="beer-list">
            ${beerList}
        </div>
        ${posts ? `
            <div class="posts-section">
                <div class="posts-title">Recent Posts</div>
                ${posts}
            </div>
        ` : ''}
    `;
    
    return card;
}

async function loadNewReleases() {
    const loading = document.getElementById('beers-loading');
    const container = document.getElementById('beers-list');
    
    loading.style.display = 'block';
    container.innerHTML = '';
    
    try {
        const suburb = document.getElementById('suburb-filter').value;
        
        // Get new beers
        let url = `${API_BASE}/beers/new?days=7`;
        const response = await fetch(url);
        const beers = await response.json();
        
        // Get venues for mapping
        const venuesResponse = await fetch(`${API_BASE}/venues`);
        const venues = await venuesResponse.json();
        const venueMap = {};
        venues.forEach(v => venueMap[v.id] = v);
        
        loading.style.display = 'none';
        
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
        
        beers.forEach(beer => {
            const brewery = venueMap[beer.brewery_id];
            const card = document.createElement('div');
            card.className = 'beer-card';
            
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
            
            const dateStr = releaseDate.toLocaleDateString('en-AU', {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            card.innerHTML = `
                <div class="beer-card-header">
                    <div>
                        <div class="venue-name">${beer.name} <span class="new-badge">NEW</span></div>
                        <div style="margin-top: 8px;">
                            <span class="beer-style">${beer.style}</span>
                            <span class="abv">${beer.abv}% ABV</span>
                        </div>
                        ${brewery ? `<div style="margin-top: 8px;"><a href="#" class="brewery-link" data-venue="${brewery.id}">${brewery.name}</a>, ${brewery.suburb}</div>` : ''}
                    </div>
                </div>
                <div style="margin-top: 12px; padding: 8px 12px; background: #f0fdf4; border-radius: 6px; border-left: 3px solid var(--success);">
                    <span style="font-size: 0.9rem; color: var(--success); font-weight: 500;">
                        📅 Released: ${dateStr} • ${timeText}
                    </span>
                </div>
                ${beer.description ? `<p style="margin-top: 12px; color: var(--text-light);">${beer.description}</p>` : ''}
            `;
            
            container.appendChild(card);
        });
    } catch (err) {
        loading.style.display = 'none';
        container.innerHTML = `<p class="empty-state">Error loading beers: ${err.message}</p>`;
    }
}

async function loadVenues() {
    const loading = document.getElementById('venues-loading');
    const container = document.getElementById('venues-list');
    
    loading.style.display = 'block';
    container.innerHTML = '';
    
    try {
        const suburb = document.getElementById('suburb-filter').value;
        
        let url = `${API_BASE}/venues`;
        if (suburb) url += `?suburb=${encodeURIComponent(suburb)}`;
        
        const response = await fetch(url);
        const venues = await response.json();
        
        loading.style.display = 'none';
        
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
        
        venues.forEach(venue => {
            const card = document.createElement('div');
            card.className = 'card';
            
            const distanceText = userLocation
                ? `<span class="distance">📍 ${calculateDistance(userLocation.lat, userLocation.lng, venue.location[0], venue.location[1]).toFixed(1)} km</span>`
                : '';
            
            card.innerHTML = `
                <div class="card-header">
                    <div>
                        <div class="venue-name">${venue.name}</div>
                        <span class="venue-type ${venue.type}">${venue.type}</span>
                    </div>
                </div>
                <div class="venue-address">${venue.address}</div>
                <div class="venue-meta">
                    <span>📍 ${venue.suburb}</span>
                    ${distanceText}
                    ${venue.instagram_handle ? `<span>📸 ${venue.instagram_handle}</span>` : ''}
                </div>
                ${venue.tags.length ? `
                    <div style="margin-top: 12px;">
                        ${venue.tags.map(tag => `<span class="beer-style" style="margin-right: 8px;">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            `;
            
            container.appendChild(card);
        });
    } catch (err) {
        loading.style.display = 'none';
        container.innerHTML = `<p class="empty-state">Error loading venues: ${err.message}</p>`;
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
        btn.textContent = 'Get Location';
        btn.disabled = false;
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            
            btn.textContent = '✓ Location Set';
            btn.disabled = false;
            
            status.innerHTML = `📍 Using your location for distance calculations<br><small>${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}</small>`;
            status.classList.remove('hidden');
            
            // Refresh with location
            loadRecommendations();
            loadVenues();
        },
        (err) => {
            status.textContent = `Could not get location: ${err.message}`;
            status.classList.remove('hidden');
            btn.textContent = 'Get Location';
            btn.disabled = false;
        }
    );
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
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
            container.innerHTML = `<p class="empty-state">Metrics not available yet. Run scraper to generate data.</p>`;
            return;
        }
        
        let html = '';
        
        // Overall stats
        html += `
            <div style="margin-bottom: 20px; padding: 16px; background: #f0fdf4; border-radius: 8px;">
                <strong>Overall Success Rate: ${data.overall?.success_rate || 0}%</strong><br>
                <span style="font-size: 0.9rem; color: var(--text-light);">
                    ${data.overall?.total_successes || 0} successes from ${data.overall?.total_attempts || 0} attempts
                    (${data.overall?.total_items || 0} items found)
                </span>
            </div>
        `;
        
        // Individual sources
        if (data.sources && Object.keys(data.sources).length > 0) {
            html += '<div class="metrics-sources">';
            for (const [sourceName, sourceData] of Object.entries(data.sources)) {
                const statusClass = sourceData.status || 'new';
                const statusIcon = statusClass === 'active' ? '✓' : statusClass === 'struggling' ? '⚠' : '?';
                
                html += `
                    <div class="metric-source ${statusClass}">
                        <div>
                            <div class="metric-name">${statusIcon} ${sourceName}</div>
                            <div class="metric-tech">${sourceData.technique}</div>
                        </div>
                        <div class="metric-stats">
                            <div class="metric-success">${sourceData.success_rate}% success</div>
                            <div class="metric-items">${sourceData.items_found} items (${sourceData.attempts} attempts)</div>
                            ${sourceData.recent_items > 0 ? `<div style="font-size: 0.75rem; color: var(--success);">+${sourceData.recent_items} recently</div>` : ''}
                        </div>
                    </div>
                `;
            }
            html += '</div>';
        } else {
            html += '<p class="empty-state">No metrics data yet. Run the scraper to collect productivity data.</p>';
        }
        
        html += `<p style="margin-top: 16px; font-size: 0.8rem; color: var(--text-light);">Generated: ${new Date(data.generated_at).toLocaleString('en-AU')}</p>`;
        
        container.innerHTML = html;
        
    } catch (err) {
        container.innerHTML = `<p class="empty-state">Error loading metrics: ${err.message}</p>`;
    }
}
