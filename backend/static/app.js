// Universal Website Scraper - Frontend
document.addEventListener('DOMContentLoaded', function() {
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
    
    // Update depth display
    depthSlider.addEventListener('input', function() {
        depthValue.textContent = this.value;
    });
    
    // Form submission
    form.addEventListener('submit', async function(e) {
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
        
        // Reset UI
        hideError();
        resultsSection.style.display = 'none';
        loading.style.display = 'block';
        scrapeBtn.disabled = true;
        
        const useJs = document.getElementById('useJs').checked;
        const maxDepth = parseInt(depthSlider.value);
        
        try {
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    use_js: useJs,
                    max_depth: maxDepth
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.error || 'Scraping failed');
            }
            
            currentResult = await response.json();
            displayResults(currentResult);
            resultsSection.style.display = 'block';
            
        } catch (error) {
            showError(`Error: ${error.message}`);
        } finally {
            loading.style.display = 'none';
            scrapeBtn.disabled = false;
        }
    });
    
    function displayResults(result) {
        // Clear previous results
        sectionsContainer.innerHTML = '';
        statsContainer.innerHTML = '';
        
        // Display statistics
        displayStats(result);
        
        // Display sections
        if (result.sections && result.sections.length > 0) {
            result.sections.forEach((section, index) => {
                const sectionElement = createSectionElement(section, index);
                sectionsContainer.appendChild(sectionElement);
            });
        }
        
        // Setup download button
        downloadBtn.onclick = function(e) {
            e.preventDefault();
            downloadJson(result);
        };
    }
    
    function displayStats(result) {
        const sections = result.sections || [];
        const errors = result.errors || [];
        const interactions = result.interactions || {};
        
        const stats = [
            { value: sections.length, label: 'Sections' },
            { value: sections.reduce((sum, s) => sum + (s.content?.links?.length || 0), 0), label: 'Links' },
            { value: sections.reduce((sum, s) => sum + (s.content?.images?.length || 0), 0), label: 'Images' },
            { value: interactions.clicks?.length || 0, label: 'Clicks' },
            { value: interactions.scrolls || 0, label: 'Scrolls' },
            { value: errors.length, label: 'Errors', error: errors.length > 0 }
        ];
        
        statsContainer.innerHTML = stats.map(stat => `
            <div class="stat-item">
                <div class="stat-value" style="color: ${stat.error ? '#fc8181' : '#667eea'}">
                    ${stat.value}
                </div>
                <div class="stat-label">${stat.label}</div>
            </div>
        `).join('');
    }
    
    function createSectionElement(section, index) {
        const sectionElement = document.createElement('div');
        sectionElement.className = 'section-card';
        sectionElement.innerHTML = `
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
                    ${truncateText(escapeHtml(section.content?.text || ''), 200)}
                </div>
                
                <div class="content-details">
                    ${section.content?.headings?.length > 0 ? `
                        <div class="detail-box">
                            <h4><i class="fas fa-heading"></i> Headings (${section.content.headings.length})</h4>
                            ${section.content.headings.map(h => `<div>• ${escapeHtml(h)}</div>`).join('')}
                        </div>
                    ` : ''}
                    
                    ${section.content?.links?.length > 0 ? `
                        <div class="detail-box">
                            <h4><i class="fas fa-link"></i> Links (${section.content.links.length})</h4>
                            ${section.content.links.slice(0, 3).map(link => `
                                <div>• <a href="${escapeHtml(link.href)}" target="_blank">${escapeHtml(link.text || 'Link')}</a></div>
                            `).join('')}
                            ${section.content.links.length > 3 ? `<div>... and ${section.content.links.length - 3} more</div>` : ''}
                        </div>
                    ` : ''}
                </div>
                
                <div class="json-viewer">
                    ${syntaxHighlight(JSON.stringify(section, null, 2))}
                </div>
            </div>
        `;
        
        return sectionElement;
    }
    
    function downloadJson(result) {
        const dataStr = JSON.stringify(result, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `scraped_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
    
    function showError(message) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
        resultsSection.style.display = 'none';
    }
    
    function hideError() {
        errorBox.style.display = 'none';
    }
    
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    function syntaxHighlight(json) {
        if (!json) return '';
        
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, 
            function(match) {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return `<span class="${cls}">${match}</span>`;
            });
    }
});

// Global function for toggling sections
function toggleSection(index) {
    const content = document.getElementById(`content-${index}`);
    const icon = document.getElementById(`icon-${index}`);
    
    content.classList.toggle('expanded');
    
    if (content.classList.contains('expanded')) {
        icon.className = 'fas fa-chevron-up';
    } else {
        icon.className = 'fas fa-chevron-down';
    }
}