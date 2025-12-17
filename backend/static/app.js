// backend/static/app.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('scraperForm');
    const urlInput = document.getElementById('urlInput');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loading = document.getElementById('loading');
    const errorBox = document.getElementById('errorBox');
    const resultsSection = document.getElementById('resultsSection');
    const sectionsContainer = document.getElementById('sectionsContainer');
    const downloadBtn = document.getElementById('downloadBtn');
    const statsContainer = document.getElementById('stats');
    const depthSlider = document.getElementById('maxDepth');
    const depthValue = document.getElementById('depthValue');

    let currentResult = null;

    if (depthSlider && depthValue) {
        depthValue.textContent = depthSlider.value;
        depthSlider.addEventListener('input', () => {
            depthValue.textContent = depthSlider.value;
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter a URL');
            return;
        }

        if (!isValidUrl(url)) {
            showError('Please enter a valid URL (http:// or https://)');
            return;
        }

        hideError();
        resultsSection.style.display = 'none';
        loading.style.display = 'block';
        scrapeBtn.disabled = true;

        const useJs = document.getElementById('useJs')?.checked ?? true;
        const maxDepth = parseInt(depthSlider?.value || '3', 10);

        try {
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    use_js: useJs,
                    max_depth: maxDepth
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err?.detail?.error || err?.detail || 'Scraping failed');
            }

            currentResult = await response.json();
            renderResults(currentResult);
            resultsSection.style.display = 'block';

        } catch (err) {
            showError(`Error: ${err.message}`);
        } finally {
            loading.style.display = 'none';
            scrapeBtn.disabled = false;
        }
    });

    function renderResults(result) {
        sectionsContainer.innerHTML = '';
        statsContainer.innerHTML = '';

        renderStats(result);

        if (Array.isArray(result.sections) && result.sections.length > 0) {
            result.sections.forEach((section, idx) => {
                sectionsContainer.appendChild(createSection(section, idx));
            });
        } else {
            sectionsContainer.innerHTML = '<p>No sections found.</p>';
        }

        setupDownload(result);
    }

    function renderStats(result) {
        const sections = result.sections || [];
        const errors = result.errors || [];
        const interactions = result.interactions || {};

        const stats = [
            { label: 'Sections', value: sections.length, icon: 'fas fa-layer-group' },
            { label: 'Links', value: sections.reduce((s, x) => s + (x.content?.links?.length || 0), 0), icon: 'fas fa-link' },
            { label: 'Images', value: sections.reduce((s, x) => s + (x.content?.images?.length || 0), 0), icon: 'fas fa-image' },
            { label: 'Clicks', value: interactions.clicks?.length || 0, icon: 'fas fa-mouse-pointer' },
            { label: 'Scrolls', value: interactions.scrolls || 0, icon: 'fas fa-mouse' },
            { label: 'Errors', value: errors.length, icon: 'fas fa-exclamation-triangle', color: errors.length ? '#f44336' : '#667eea' }
        ];

        statsContainer.innerHTML = stats.map(s => `
            <div class="stat-item">
                <i class="${s.icon}" style="color:${s.color || '#667eea'}"></i>
                <div class="stat-value">${s.value}</div>
                <div class="stat-label">${s.label}</div>
            </div>
        `).join('');
    }

    function createSection(section, index) {
        const el = document.createElement('div');
        el.className = 'section-card';

        el.innerHTML = `
            <div class="section-header" onclick="toggleSection(${index})">
                <div>
                    <div class="section-title">${escapeHtml(section.label)}</div>
                    <div class="section-meta">
                        <span class="section-type">${section.type}</span>
                        <span>ID: ${section.id}</span>
                        <span>${section.content?.text?.length || 0} chars</span>
                    </div>
                </div>
                <i class="fas fa-chevron-down" id="icon-${index}"></i>
            </div>
            <div class="section-content" id="content-${index}">
                <div class="content-preview">
                    ${truncate(escapeHtml(section.content?.text || ''), 200)}
                </div>

                <div class="content-details">
                    ${renderList('Headings', section.content?.headings)}
                    ${renderLinks(section.content?.links)}
                    ${renderImages(section.content?.images)}
                </div>

                <h4>Raw HTML:</h4>
                <div class="json-viewer">
                    <pre>${escapeHtml(section.rawHtml?.slice(0, 500) || '')}${section.rawHtml?.length > 500 ? '...' : ''}</pre>
                </div>

                <h4>Full JSON:</h4>
                <div class="json-viewer">
                    <pre>${highlight(JSON.stringify(section, null, 2))}</pre>
                </div>
            </div>
        `;
        return el;
    }

    function renderList(title, items = []) {
        if (!items.length) return '';
        return `
            <div class="detail-box">
                <h4>${title} (${items.length})</h4>
                ${items.map(i => `<div>• ${escapeHtml(i)}</div>`).join('')}
            </div>
        `;
    }

    function renderLinks(links = []) {
        if (!links.length) return '';
        return `
            <div class="detail-box">
                <h4>Links (${links.length})</h4>
                ${links.slice(0, 3).map(l =>
                    `<div>• <a href="${escapeHtml(l.href)}" target="_blank">${escapeHtml(l.text || 'Link')}</a></div>`
                ).join('')}
            </div>
        `;
    }

    function renderImages(images = []) {
        if (!images.length) return '';
        return `
            <div class="detail-box">
                <h4>Images (${images.length})</h4>
                ${images.slice(0, 2).map(img =>
                    `<div>• <a href="${escapeHtml(img.src)}" target="_blank">${escapeHtml(img.alt || 'Image')}</a></div>`
                ).join('')}
            </div>
        `;
    }

    function setupDownload(result) {
        downloadBtn.onclick = (e) => {
            e.preventDefault();
            const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scraped_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        };
    }

    function showError(msg) {
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
    }

    function hideError() {
        errorBox.style.display = 'none';
    }

    function isValidUrl(str) {
        try { new URL(str); return true; } catch { return false; }
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
    }

    function truncate(str, n) {
        return str.length > n ? str.slice(0, n) + '...' : str;
    }

    function highlight(json) {
        return json
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+)/g, m => {
                let c = 'json-number';
                if (m.startsWith('"')) c = m.endsWith(':') ? 'json-key' : 'json-string';
                else if (/true|false/.test(m)) c = 'json-boolean';
                else if (/null/.test(m)) c = 'json-null';
                return `<span class="${c}">${m}</span>`;
            });
    }
});

function toggleSection(i) {
    const c = document.getElementById(`content-${i}`);
    const ic = document.getElementById(`icon-${i}`);
    c.classList.toggle('expanded');
    ic.className = c.classList.contains('expanded')
        ? 'fas fa-chevron-up'
        : 'fas fa-chevron-down';
}
