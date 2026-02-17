
const API_BASE = '/api';
let issueData = null;
let currentPage = 0;

document.addEventListener('DOMContentLoaded', () => {
    loadIssue();
    
    // Navigation
    document.getElementById('nav-prev').addEventListener('click', prevPage);
    document.getElementById('nav-next').addEventListener('click', nextPage);
    
    // Keyboard nav
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') prevPage();
        if (e.key === 'ArrowRight') nextPage();
    });

    // Initial scale adjustment
    adjustMagazineScale();
    window.addEventListener('resize', adjustMagazineScale);
});

function adjustMagazineScale() {
    const wrapper = document.getElementById('magazine-container');
    const spread = document.getElementById('page-spread');
    if (!wrapper || !spread) return;

    // The desired width of the magazine page
    const baseWidth = 770; 
    const padding = 20; // safe zone padding
    
    // Available width
    const availableWidth = wrapper.clientWidth - padding;
    
    // Only scale down, never up (unless we want to zoom, but pixelation risks)
    let scale = availableWidth / baseWidth;
    if (scale > 1) scale = 1;

    // Apply scale
    spread.style.transform = `scale(${scale})`;
    spread.style.transformOrigin = 'top center';
    
    // Because scaling doesn't affect flow layout flow-size, we need to adjust margins
    // to remove the extra whitespace created by scaling down.
    // The height shrinks physically but visually takes less space.
    // However, the container might scroll.
    
    // Actually, setting marginBottom might be enough for vertical flow,
    // but horizontal centering is handled by the parent flex and transform-origin.
    
    // Note: The spread has a fixed height of 1190px.
    // We can reduce the effective height of the container or margin to bring controls up closer.
    const baseHeight = 1190;
    const scaledHeight = baseHeight * scale;
    
    // We can explicitly set the height of the spread in flow to match visual height?
    // No, transforms don't change layout size. 
    // We can use a negative margin bottom to pull content up.
    spread.style.marginBottom = `${-(baseHeight - scaledHeight)}px`;
}

async function loadIssue() {
    try {
        const res = await fetch(`${API_BASE}/issue/latest`);
        if (!res.ok) {
            // Try to parse error details
            let errorDetails = "Unknown error";
            try {
                // Read text first to avoid stream locking issues
                const textBody = await res.text();
                try {
                    const jsonErr = JSON.parse(textBody);
                    // Use pretty printing if it's JSON
                    errorDetails = JSON.stringify(jsonErr, null, 2);
                } catch {
                    // It was just text/HTML
                    errorDetails = textBody.slice(0, 800); // Limit length
                }
            } catch(e) {
                errorDetails = "Could not read response body: " + e.message;
            }
            throw new Error(`Failed to load issue (${res.status}). Details: ${errorDetails}`);
        }
        issueData = await res.json();
        
        renderPage(0); // Start at cover
        updateControls();
    } catch (err) {
        document.getElementById('page-spread').innerHTML = `
            <div class="error-screen" style="padding: 20px; overflow: auto; max-height: 80vh;">
                <h2>Issue Not Found</h2>
                <p>Please run the generator script on the backend or check deployment.</p>
                <code style="display:block; margin:1em 0; padding:10px; background:#222;">python scripts/magazine_generator.py</code>
                <div style="margin-top:20px; font-size: 0.8em; color: #ff6b6b; white-space: pre-wrap; text-align: left; background: #000; padding: 10px;">${err.message}</div>
            </div>
        `;
    }
}

function renderPage(index) {
    if (!issueData || !issueData.pages[index]) return;
    
    const page = issueData.pages[index];
    const container = document.getElementById('page-spread');
    
    // Fade out effect could go here
    
    let html = '';
    
    switch(page.type) {
        case 'cover':
            html = renderCover(page);
            break;
        case 'toc':
            html = renderTOC(page);
            break;
        case 'article':
            html = renderArticle(page);
            break;
        case 'brewery-spotlight':
            html = renderBrewerySpotlight(page);
            break;
        case 'top10-spotlight':
            html = renderTop10Spotlight(page);
            break;
        case 'top10-list':
            html = renderTop10List(page);
            break;
        case 'full-ad':
            html = renderFullAd(page);
            break;
        case 'full-photo-page':
            html = renderFullPhoto(page);
            break;
        case 'fresh-on-tap':
            html = renderFreshOnTap(page);
            break;
        case 'list-page':
            html = renderListPage(page); // Needed separate fetch? Or static?
            break;
        case 'placeholder':
             html = `<div class="magazine-page placeholder-page"><h1>Reserved for Content</h1></div>`;
             break;
        default:
            html = `<div class="magazine-page"><h1>Unknown Page Type</h1></div>`;
    }
    
    container.innerHTML = html;
    
    // Update number display
    document.getElementById('page-number-display').textContent = index === 0 ? 'Cover' : `Page ${index + 1}`;
    
    // Update progress bar
    const total = issueData.pages.length;
    const pct = ((index + 1) / total) * 100;
    document.getElementById('mag-progress-bar').style.width = `${pct}%`;
    document.getElementById('total-pages-display').textContent = `${total} Pages`;
    
    currentPage = index;
    updateControls();
    
    // Scroll to top of page
    document.getElementById('magazine-container').scrollTop = 0;
}

function updateControls() {
    const prevBtn = document.getElementById('nav-prev');
    const nextBtn = document.getElementById('nav-next');
    
    if (!issueData) return;
    
    prevBtn.disabled = currentPage === 0;
    nextBtn.disabled = currentPage >= issueData.pages.length - 1;
    
    prevBtn.style.opacity = currentPage === 0 ? 0.3 : 1;
    nextBtn.style.opacity = currentPage >= issueData.pages.length - 1 ? 0.3 : 1;
}

function prevPage() {
    if (currentPage > 0) renderPage(currentPage - 1);
}

function nextPage() {
    if (issueData && currentPage < issueData.pages.length - 1) renderPage(currentPage + 1);
}

// --- Renderers ---

function getBeerImage(text) {
    // Deterministic random image based on text
    const images = [
        'https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1000&q=80',
        'https://images.unsplash.com/photo-1575037614876-c38a4d44f5b8?w=1000&q=80',
        'https://images.unsplash.com/photo-1567696911980-2eed69a46042?w=1000&q=80',
        'https://images.unsplash.com/photo-1559526323-cb2f2fe2591b?w=1000&q=80',
        'https://images.unsplash.com/photo-1518176258769-f227c798150e?w=1000&q=80',
        'https://images.unsplash.com/photo-1436076863939-06870fe779c2?w=1000&q=80',
        'https://images.unsplash.com/photo-1608270586620-248524c67de9?w=1000&q=80',
        'https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=1000&q=80'
    ];
    let hash = 0;
    const str = text || 'beer';
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return images[Math.abs(hash) % images.length];
}

function renderCover(page) {
    return `
        <div class="magazine-page cover-page" style="background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url('${page.main_image}')">
            <div class="cover-header">
                <div class="issue-no">ISSUE ${page.issue}</div>
                <div class="issue-date">${page.date}</div>
            </div>
            <div class="cover-content">
                <h1 class="cover-title">SYDNEY<br>BEER<br>WEEKLY</h1>
                <div class="cover-feature">
                    <span>FEATURED</span>
                    <h2>${page.cover_story}</h2>
                </div>
            </div>
        </div>
    `;
}

function renderTOC(page) {
    const publishDate = issueData && issueData.generated_at 
        ? new Date(issueData.generated_at).toLocaleString('en-AU', { 
            dateStyle: 'medium', 
            timeStyle: 'short' 
          })
        : '';

    const listHtml = page.contents.map(item => `
        <div class="toc-item" onclick="renderPage(${item.page - 1})"> <!-- 0-based index -->
            <span class="toc-title">${item.title}</span>
            <span class="toc-page-num">${item.page}</span>
        </div>
    `).join('');
    
    // Check for background image
    const bgStyle = page.background_image 
        ? `background-image: url('${page.background_image}')` 
        : '';
    const wrapperClass = page.background_image ? 'spotlight-page' : 'magazine-page toc-page';
    
    if (page.background_image) {
         return `
              <div class="magazine-page spotlight-page toc-page">
                  <div class="spotlight-bg" style="background-image: url('${page.background_image}'); filter: brightness(0.6);"></div>
                  <div class="spotlight-overlay" style="align-items: flex-start; padding: 60px; background: linear-gradient(to right, rgba(0,0,0,0.85) 40%, rgba(0,0,0,0.5) 100%);">
                    <h2 class="page-header" style="border-bottom-color: white; margin-bottom: 40px;">In This Issue</h2>
                    <div class="toc-list" style="width: 100%; max-width: 600px;">
                        ${listHtml}
                    </div>
                    <div class="masthead-credits" style="margin-top: auto; color: #ccc;">
                        <h3>Sydney Beer Weekly</h3>
                        <p>Editor-in-Chief: Chris Shoesmith</p>
                        <p>Generated by: Github Copilot</p>
                        <p>Published: ${publishDate}</p>
                        <p>Data: Untappd & Website Scrapers</p>
                    </div>
                </div>
            </div>
        `;
    }

    return `
        <div class="magazine-page toc-page">
            <h2 class="page-header">In This Issue</h2>
            <div class="toc-list">
                ${listHtml}
                <div class="toc-item ads">
                    <span class="toc-title">Advertisements</span>
                    <span class="toc-page">Var</span>
                </div>
            </div>
            <div class="masthead-credits">
                <h3>Sydney Beer Weekly</h3>
                <p>Editor-in-Chief: Chris Shoesmith</p>
                <p>Generated by: Github Copilot</p>
                <p>Published: ${publishDate}</p>
                <p>Data: Untappd & Website Scrapers</p>
            </div>
        </div>
    `;
}

function renderArticle(page) {
    let layoutClass = page.layout || 'single-col';
    
    // Sidebar logic for "Right Sidebar" layouts
    let sidebarHtml = '';
    if (page.sidebar) {
        if (page.sidebar.data) {
            // Fact File style (Object)
            const rows = Object.entries(page.sidebar.data).map(([k,v]) => `
                <div class="sidebar-row">
                    <strong>${k}:</strong> <span>${v}</span>
                </div>
            `).join('');
            sidebarHtml += `
                <div class="sidebar-box">
                    <h4>Fast Facts</h4>
                    <div class="sidebar-content">${rows}</div>
                </div>
            `;
        } 
        
        if (page.sidebar.list) {
            // List style (Array)
            const items = page.sidebar.list.map(i => `<li>${i}</li>`).join('');
            sidebarHtml += `
                <div class="sidebar-box">
                    <h4>Local Vibes</h4>
                    <ul class="sidebar-list">${items}</ul>
                </div>
            `;
        }
    }
    
    // Handle Text-Only page (continuation)
    if (layoutClass === 'feature-text-only') {
        return `
            <div class="magazine-page article-page ${layoutClass}">
                <div class="article-body-wrapper">
                    <div class="article-body drop-cap serif">
                        ${formatBody(page.body)}
                    </div>
                </div>
                ${sidebarHtml ? `<div class="article-sidebar">${sidebarHtml}</div>` : ''}
                ${page.ad_bottom ? '<div class="internal-ad">Supported by Local Brewers</div>' : ''}
            </div>
        `;
    }

    const sectionTag = page.headline.includes('Editor') ? 'OPINION' : 'FEATURE';

    // Highlight Background Logic
    if (page.background_image) {
         return `
            <div class="magazine-page spotlight-page brewery-focus">
                <div class="spotlight-bg" style="background-image: url('${page.background_image}'); filter: brightness(0.6);"></div>
                <div class="spotlight-overlay" style="background: linear-gradient(to right, rgba(0,0,0,0.85) 40%, rgba(0,0,0,0.5) 100%);">
                    <div class="spotlight-section-tag">${sectionTag}</div>
                    <h2 class="spotlight-title big-title" style="font-size: 2.5rem;">${page.headline}</h2>
                     ${page.subhead ? `<h3 class="spotlight-brewery">${page.subhead}</h3>` : ''}
                    
                    <div class="article-main-flex" style="margin-top: 20px;">
                        <div class="spotlight-body serif" style="color: #ddd;">
                            ${formatBody(page.body)}
                        </div>
                        ${sidebarHtml ? `<div class="spotlight-sidebar-floating"><div class="info-card">${sidebarHtml}</div></div>` : ''}
                    </div>
                     ${page.footer ? `<div class="article-footer" style="color: #ccc; margin-top: auto;">${page.footer}</div>` : ''}
                </div>
            </div>
        `;
    }

    return `
        <div class="magazine-page article-page ${layoutClass}">
            ${page.image ? `<div class="article-hero-img"><img src="${page.image}" loading="lazy"></div>` : ''}
            <div class="article-content-wrapper">
                <div class="article-header-block">
                    <h5 class="section-tag">${sectionTag}</h5>
                    <h2 class="article-headline-lg">${page.headline}</h2>
                    ${page.subhead ? `<h3 class="article-subhead">${page.subhead}</h3>` : ''}
                </div>
                <div class="article-main-flex">
                    <div class="article-body serif">
                        ${formatBody(page.body)}
                    </div>
                    ${sidebarHtml ? `<div class="article-sidebar">${sidebarHtml}</div>` : ''}
                </div>
                ${page.footer ? `<div class="article-footer">${page.footer}</div>` : ''}
            </div>
        </div>
    `;
}

function renderTop10Spotlight(page) {
    if (!page.data || !page.data.beer) return '<div class="magazine-page"><h1>Data Missing</h1></div>';

    const beer = page.data.beer;
    const article = page.data.article || { body: "No article content available." };
    
    // Image selection logic
    let image = getBeerImage(beer.name);
    if (beer.details && beer.details.recent_photos && beer.details.recent_photos.length > 0) {
        image = beer.details.recent_photos[0];
    }

    // Technical Stats (Use provided or placeholder)
    const abv = (beer.details && beer.details.abv) ? beer.details.abv.toFixed(1) : '-';
    
    // For visual bars, if data is missing, show 0 height
    const abvHeight = abv === '-' ? 0 : Math.min((parseFloat(abv) / 15) * 100, 100);
    const ibu = (beer.details && beer.details.ibu) || '-';
    // If IBU is missing, don't fallback to random.
    const ibuHeight = ibu === '-' ? 0 : Math.min((parseInt(ibu) / 100) * 100, 100);
    
    // Truncate overly long descriptions so they don't overflow the page
    let displayBody = article.body;
    if (displayBody && displayBody.length > 900) {
        const cut = displayBody.substring(0, 900);
        const lastDot = cut.lastIndexOf('.');
        displayBody = (lastDot > 500 ? cut.substring(0, lastDot + 1) : cut) + " ...";
    }
    
    return `
        <div class="magazine-page spotlight-page">
            <div class="spotlight-bg" style="background-image: url('${image}')"></div>
            <div class="spotlight-overlay">
                
                <div class="spotlight-header-row" style="display:flex; justify-content:space-between; align-items:flex-start; width:100%; margin-bottom:20px;">
                    <div class="rank-badge-lg">#${page.rank}</div>
                    
                    <div class="tech-specs-container" style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; backdrop-filter:blur(5px);">
                        <div class="list-stats-container" style="height:120px; margin:0;">
                            <div class="stat-bar-group" style="width:45px;">
                                <div class="stat-value" style="font-size:1.4rem;">${abv}%</div>
                                <div class="stat-bar abv" style="height: ${abvHeight}%"></div>
                                <div class="stat-label" style="font-size:0.9rem;">ABV</div>
                            </div>
                            <div class="stat-bar-group" style="width:45px;">
                                <div class="stat-value" style="font-size:1.4rem;">${ibu}</div>
                                <div class="stat-bar ibu" style="height: ${ibuHeight}%"></div>
                                <div class="stat-label" style="font-size:0.9rem;">IBU</div>
                            </div>
                        </div>
                    </div>
                </div>

                <h2 class="spotlight-title">${beer.name}</h2>
                <h3 class="spotlight-brewery">${beer.brewery}</h3>
                
                <div class="spotlight-body serif">
                     ${formatBody(displayBody)}
                </div>
                
                <div class="spotlight-stats">
                    <div class="stat-box">
                        <div class="stat-val">${Math.round(beer.score)}</div>
                        <div class="stat-lbl">Score</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val">${beer.rating || '-'}</div>
                        <div class="stat-lbl">Untappd</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderBrewerySpotlight(page) {
    // Reusing the spotlight styling but with more data
    
    // Construct Sidebar HTML (Fact File + Local Vibes)
    let sidebarContent = '';
    
    if (page.sidebar && page.sidebar.data) {
        sidebarContent += Object.entries(page.sidebar.data).map(([k,v]) => 
            `<div class="stat-row"><strong>${k}:</strong> ${v}</div>`
        ).join('');
    }
    
    if (page.sidebar && page.sidebar.list && page.sidebar.list.length > 0) {
        sidebarContent += '<div class="stat-separator"></div>';
        sidebarContent += page.sidebar.list.map(i => 
            `<div class="stat-row">✓ ${i}</div>`
        ).join('');
    }

    return `
        <div class="magazine-page spotlight-page brewery-focus">
            <div class="spotlight-bg" style="background-image: url('${page.image}')"></div>
            <div class="spotlight-overlay">
                <div class="spotlight-section-tag">BREWERY FOCUS</div>
                <h2 class="spotlight-title big-title">${page.headline}</h2>
                <h3 class="spotlight-brewery">${page.subhead}</h3>
                
                <div class="spotlight-layout">
                    <div class="spotlight-body serif">
                         ${formatBody(page.body)}
                    </div>
                    
                    <div class="spotlight-sidebar-floating">
                         <div class="info-card">
                            <h4>Fast Facts & Vibes</h4>
                            ${sidebarContent}
                         </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderTop10List(page) {
    const itemsHtml = page.items.map(item => {
        // Image logic: 1) explicit item.image 2) recent photo from scraper 3) fallback deterministic
        let thumb = item.image;
        if (!thumb && item.beer.details && item.beer.details.recent_photos && item.beer.details.recent_photos.length > 0) {
            thumb = item.beer.details.recent_photos[0];
        }
        if (!thumb) thumb = getBeerImage(item.beer.name);
        
        // Show full article body instead of truncated excerpt
        const fullBody = item.article && item.article.body 
            ? item.article.body 
            : "No review available for this beer yet.";
        
        // Format the body for paragraphs
        const formattedBody = formatBody(fullBody);
        
        return `
        <div class="list-item-card full-story-card">
            <div class="list-rank-circle">#${item.rank}</div>
            <div class="list-thumb" style="background-image: url('${thumb}')"></div>
            <div class="list-info-col">
                <div class="list-header-row">
                    <div>
                        <h4>${item.beer.name}</h4>
                        <div class="list-meta">${item.beer.brewery} • ${item.beer.style}</div>
                    </div>
                     <div class="list-score-badge-mini">
                        <span>${Math.round(item.beer.score)}</span>
                    </div>
                </div>
                <div class="list-full-body serif">${formattedBody}</div>
            </div>
        </div>
    `}).join('');
    
    return `
        <div class="magazine-page list-page-generic">
            <h2 class="page-header">Top 10 Countdown</h2>
            <div class="ranking-grid full-story-grid">
                ${itemsHtml}
            </div>
            ${page.footer_notes ? `<div class="page-footer-note">${page.footer_notes}</div>` : ''}
        </div>
    `;
}

function renderFullAd(page) {
    return `
        <div class="magazine-page full-ad-page" style="background-image: url('${page.image}')">
            <div class="ad-overlay">
                <span class="ad-tag">Advertisement</span>
                <h3>${page.brand}</h3>
            </div>
        </div>
    `;
}

/* --- Mosaic Zoom Logic --- */
function toggleMosaicZoom(e, img) {
    if (img.classList.contains('zoomed')) {
        img.style.transform = '';
        img.classList.remove('zoomed');
    } else {
        const rect = img.parentElement.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Scale factor: 4x allows viewing 80px tiles as ~320px details (or less if base img is small)
        const scale = 4;
        
        // Calculate transform origin based on click percentage
        const xPercent = (x / rect.width) * 100;
        const yPercent = (y / rect.height) * 100;
        
        img.style.transformOrigin = `${xPercent}% ${yPercent}%`;
        img.style.transform = `scale(${scale})`;
        img.classList.add('zoomed');
    }
}

function renderFullPhoto(page) {
    const bio = page.bio || { name: 'Unknown', age: '?', hobbies: 'Drinking beer', favorite_style: 'Lager', quote: 'Cheers!' };
    
    return `
        <div class="magazine-page full-photo-page">
            <!-- Title Bar "Outside" the picture -->
            <div class="page3-title-bar">
                <h3>${page.caption}</h3>
                <p>${page.subcaption}</p>
            </div>

            <!-- Photomosaic: beer check-in photos arranged to form the portrait -->
            <div class="page3-image-wrapper">
                <img class="mosaic-image" src="${page.image}" alt="Beer Photomosaic" onclick="toggleMosaicZoom(event, this)" title="Click to Zoom" />
                
                <!-- Bio Card at Bottom Right -->
                <div class="bio-card">
                    <div class="bio-header">
                        <h2 class="bio-name">${bio.name}, ${bio.age}</h2>
                        <div class="bio-quote">"${bio.quote}"</div>
                    </div>
                    <div class="bio-details">
                        <div class="bio-row"><strong>Hobbies:</strong> ${bio.hobbies}</div>
                        <div class="bio-row"><strong>Fave Style:</strong> ${bio.favorite_style}</div>
                    </div>
                </div>

            </div>
            
            <div class="page-number-squeezed" style="color:white; text-shadow:0 2px 5px rgba(0,0,0,0.5); bottom: 10px; right: 20px; z-index:20;">3</div>
        </div>
    `;
}

function renderFreshOnTap(page) {
    const beers = page.data.top_beers || [];
    const venues = page.data.top_venues || [];
    
    // Render Beers Rows
    const beerRows = beers.map((b, i) => `
        <tr class="beer-row">
            <td class="col-rank"><span class="venue-rank">#${i+1}</span></td>
            <td class="col-name"><strong>${b.name}</strong><br><span class="beer-detail">${b.brewery} • ${b.style}</span></td>
            <td class="col-rating">${b.rating}</td>
        </tr>
    `).join('');
    
    // Render Venue Rows
    const venueRows = venues.map((v, i) => `
        <li class="venue-item">
            <span class="venue-rank">#${i+1}</span>
            <div class="venue-info">
                <span class="venue-name">${v.name}</span>
                <span class="venue-count">${v.count} updates</span>
            </div>
        </li>
    `).join('');

    // Render Suburb Rows (New)
    const suburbRows = (page.data.top_suburbs || []).map((s, i) => `
        <li class="venue-item">
            <span class="venue-rank">#${i+1}</span>
            <div class="venue-info">
                <span class="venue-name">${s.name}</span>
                <span class="venue-count">${s.count} mentions</span>
            </div>
        </li>
    `).join('');

    const bgStyle = page.background_image 
        ? `background-image: url('${page.background_image}'); filter: brightness(0.95);` 
        : '';
        
    const wrapperClass = page.background_image ? 'magazine-page spotlight-page' : 'magazine-page fresh-page';
    const contentStyle = page.background_image 
        ? 'background: linear-gradient(to right, rgba(0,0,0,0.6) 40%, rgba(0,0,0,0.2) 100%); padding: 40px; height: 100%; color: white; display:flex; flex-direction:column;' 
        : '';

    return `
        <div class="${wrapperClass}">
            ${page.background_image ? `<div class="spotlight-bg" style="${bgStyle}"></div>` : ''}
            <div style="${contentStyle}; position: relative; z-index: 2;">
            
                <div class="fresh-header">
                    <h2>Fresh on Tap</h2>
                    <div class="fresh-sub">Live data from Sydney's best venues</div>
                </div>
                
                <div class="fresh-layout">
                    <div class="fresh-col-main">
                        <h3 class="section-label">Top 10 Rated</h3>
                        <table class="fresh-table ${page.background_image ? 'dark-mode' : ''}">
                            <thead>
                                <tr>
                                    <th width="10%">#</th>
                                    <th width="75%">Beer</th>
                                    <th width="15%">Rating</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${beerRows}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="fresh-col-side">
                        <div style="margin-bottom: 40px;">
                            <h3 class="section-label">Most Active Venues</h3>
                            <ul class="venue-list">
                                ${venueRows}
                            </ul>
                        </div>

                        <div>
                            <h3 class="section-label">Top 5 Suburbs</h3>
                            <ul class="venue-list">
                                ${suburbRows}
                            </ul>
                        </div>
                    </div>
                </div>
            
            </div>
        </div>
    `;
}

function renderListPage(page) {
    return `
        <div class="magazine-page plain-text-page">
            <h2 class="page-header">${page.headline}</h2>
            <div class="simple-list" id="new-releases-container">
                <p>Loading latest arrivals...</p>
            </div>
        </div>
    `;
}

// Add fetch for new releases logic in the render
document.addEventListener('DOMNodeInserted', (e) => {
    if (e.target.id === 'new-releases-container' || (e.target.querySelector && e.target.querySelector('#new-releases-container'))) {
        const container = document.getElementById('new-releases-container');
        if (container && container.innerHTML.includes('Loading')) {
             fetch('/api/beers/new').then(r=>r.json()).then(data => {
               container.innerHTML = data.slice(0,12).map(b => 
                   '<div class="simple-item"><div class="item-name">' + b.name + '</div><div class="item-brewery">' + b.brewery + '</div></div>'
               ).join('');
           }).catch(e => container.innerHTML = 'Error loading data');
        }
    }
});

function formatBody(text) {
    if (!text) return '';
    return text.split('\n\n').map(p => `<p>${p}</p>`).join('');
}

// === Admin Logic ===
function toggleAdmin() {
    const modal = document.getElementById('admin-modal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeAdmin() {
    document.getElementById('admin-modal').style.display = 'none';
    document.body.style.overflow = '';
}

async function loadExistingVenues() {
    const listDiv = document.getElementById('existing-venues-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div style="padding:10px; color:#aaa;">Loading venues...</div>';
    try {
        // Use the new admin endpoint
        const response = await fetch('/api/admin/venues-list'); 
        if (!response.ok) throw new Error("Failed to fetch admin list");
        
        const data = await response.json();
        const { untappd, auto } = data;
        
        let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
        
        // Auto-discovered (Pending/New)
        if (auto && auto.length > 0) {
            html += '<div style="font-size:0.8rem; color:#f1c40f; margin-top:5px; margin-bottom:2px; font-weight:bold; border-bottom:1px solid #444;">New / Auto-Discovered</div>';
            html += auto.map(v => `
                <div style="display:flex; justify-content:space-between; align-items:center; background:#222; padding:5px; border-radius:4px; margin-bottom:2px;">
                    <div style="overflow:hidden; padding-right:10px;">
                        <div style="font-size:0.85rem; font-weight:bold; color:#ddd; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${v.name}">${v.name}</div>
                        <div style="font-size:0.75rem; color:#888;">${v.location || 'Unknown'} (${v.status})</div>
                    </div>
                    <button onclick="deleteVenue('auto', '${v.id}', '${v.name.replace(/'/g, "\\'")}')" 
                            style="background:#c0392b; color:white; border:none; border-radius:3px; padding:3px 8px; font-size:0.7rem; cursor:pointer;">
                        DEL
                    </button>
                </div>
            `).join('');
        }
        
        // Confirmed (Untappd)
        if (untappd && untappd.length > 0) {
             html += '<div style="font-size:0.8rem; color:#3498db; margin-top:10px; margin-bottom:2px; font-weight:bold; border-bottom:1px solid #444;">Tracked Venues (Untappd)</div>';
             html += untappd.map(v => `
                <div style="display:flex; justify-content:space-between; align-items:center; background:#222; padding:5px; border-radius:4px; margin-bottom:2px;">
                    <div style="overflow:hidden; padding-right:10px;">
                        <div style="font-size:0.85rem; font-weight:bold; color:#ddd; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${v.name}">${v.name}</div>
                        <div style="font-size:0.75rem; color:#888;">ID: ${v.untappd_id}</div>
                    </div>
                    <button onclick="deleteVenue('untappd', '${v.id}', '${v.name.replace(/'/g, "\\'")}')" 
                            style="background:#c0392b; color:white; border:none; border-radius:3px; padding:3px 8px; font-size:0.7rem; cursor:pointer;">
                        DEL
                    </button>
                </div>
             `).join('');
        }
        
        html += '</div>';
        listDiv.innerHTML = html;
        
    } catch (e) {
        console.error(e);
        listDiv.innerHTML = '<div style="color:red; padding:10px;">Error loading venues. Check console.</div>';
    }
}

async function deleteVenue(source, id, name) {
    if (!confirm(`Are you sure you want to delete "${name}" from the ${source} list? This will prevent it from appearing in future issues.`)) return;
    
    // Optimistic UI update could be done here, but reload is safer
    const listDiv = document.getElementById('existing-venues-list');
    const originalContent = listDiv.innerHTML;
    listDiv.innerHTML = '<div style="padding:10px; color:#aaa;">Deleting...</div>';
    
    try {
        const response = await fetch(`/api/admin/venues/${source}/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Success
            loadExistingVenues(); // Reload list
        } else {
            const data = await response.json();
            alert('Delete failed: ' + (data.error || 'Unknown error'));
            listDiv.innerHTML = originalContent;
        }
    } catch (e) {
        alert('Error: ' + e.message);
        listDiv.innerHTML = originalContent;
    }
}

function verifyAdmin() {
    const pass = document.getElementById('admin-pw').value;
    if (pass === 'Admin_123') {
        document.getElementById('admin-login-step').style.display = 'none';
        document.getElementById('admin-content-step').style.display = 'block';
        loadExistingVenues();
    } else {
        document.getElementById('login-error').style.display = 'block';
    }
}

async function searchVenues() {
    const query = document.getElementById('venue-search').value;
    const resultsDiv = document.getElementById('search-results');
    
    if (query.length < 3) return;

    // Use full path + version to debug
    const endpoint = `/api/find_venue?q=${encodeURIComponent(query)}`;
    resultsDiv.innerHTML = `<div style="padding:10px; color:#aaa; text-align:center;">Searching via ${endpoint}...</div>`;
    
    try {
        // Simplified route to avoid Vercel path issues
        const response = await fetch(endpoint);
        if (!response.ok) {
            let errorMsg = `Search failed (${response.status} at ${endpoint})`;
            try { 
                // Try to get JSON error
                const errData = await response.json(); 
                if (errData.error) errorMsg = errData.error;
            } catch(e) {
                // Not JSON, probably HTML timeout page
                // Try to get text to see if it provides a clue
                try {
                    const text = await response.text();
                    if (text.includes("TIMED_OUT")) errorMsg = "Server Timed Out (Untappd Slow)";
                    else if (text.includes("FUNCTION_INVOCATION_TIMEOUT")) errorMsg = "Vercel Function Timeout";
                    else errorMsg = `Server Error ${response.status} (Raw Text)`;
                } catch(textErr) {}
            }
            throw new Error(errorMsg);
        }
        const results = await response.json();
        
        if (results.length === 0) {
            resultsDiv.innerHTML = '<div style="padding:10px; color:#aaa; text-align:center;">No venues found near Sydney.</div>';
            return;
        }

        resultsDiv.innerHTML = results.map(v => `
            <div style="padding:10px; border-bottom:1px solid #444; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="color:white;">${v.name}</strong>
                    <div style="font-size:0.8rem; color:#888;">${v.address}</div>
                </div>
                <button onclick="addVenue('${v.id}', '${v.name.replace(/'/g, "\\'")}')" 
                        style="padding:5px 10px; background:var(--mag-accent); color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                    ADD
                </button>
            </div>
        `).join('');
        
    } catch (e) {
        resultsDiv.innerHTML = `<div style="padding:10px; color:red;">Error: ${e.message}</div>`;
    }
}

async function generateMagazine() {
    if (!confirm('This will trigger a new magazine generation. It may take 30-60 seconds. Continue?')) return;
    
    const btn = document.getElementById('btn-generate-mag');
    const status = document.getElementById('gen-status');
    
    btn.disabled = true;
    btn.style.opacity = '0.5';
    btn.innerText = 'GENERATING... PLEASE WAIT';
    status.innerText = 'Running AI generation script...';
    
    try {
        const styleIdx = document.getElementById('page3-style')?.value || '1';
        const styleMap = ['business', 'girl_next_door', 'lingerie'];
        const page3Style = styleMap[parseInt(styleIdx)] || 'girl_next_door';
        
        // Get mode (Mosaic vs Natural)
        const modeRadio = document.querySelector('input[name="page3-mode"]:checked');
        const page3Mode = modeRadio ? modeRadio.value : 'mosaic';

        const response = await fetch('/api/admin/generate-magazine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ page3_style: page3Style, page3_mode: page3Mode })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            status.innerHTML = `<span style="color:#2ecc71">Generation Complete! Issue #${data.issue_number || '?'}, ${data.pages_count || '?'} pages. Refreshing...</span>`;
            console.log('Generate response:', JSON.stringify(data, null, 2));
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            console.error('Generate failed:', JSON.stringify(data, null, 2));
            throw new Error(data.error || 'Unknown error');
        }
        
    } catch (e) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.innerText = 'GENERATE NEW MAGAZINE';
        status.innerHTML = `<span style="color:#ff6b6b">Error: ${e.message}</span>`;
    }
}

async function addVenue(id, name) {
    if (!confirm(`Add ${name} to tracking list?`)) return;
    
    try {
        const response = await fetch('/api/admin/venues/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id, name })
        });
        
        if (response.ok) {
            alert(`Successfully added ${name}!`);
            document.getElementById('venue-search').value = '';
            document.getElementById('search-results').innerHTML = '';
            loadExistingVenues();
        } else {
            alert('Failed to add venue');
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}


