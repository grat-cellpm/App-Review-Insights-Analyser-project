document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Lucide icons
    lucide.createIcons();

    try {
        // Use a timestamp to prevent the browser from caching data.json
        const response = await fetch('data.json?t=' + new Date().getTime());
        const data = await response.json();
        
        // Update KPIs
        document.getElementById('kpi-total-reviews').textContent = data.total_reviews_processed;
        document.getElementById('kpi-total-clusters').textContent = data.total_clusters_found;

        const clustersContainer = document.getElementById('clusters-container');
        const template = document.getElementById('cluster-card-template');

        data.clusters.forEach((cluster, index) => {
            const clone = template.content.cloneNode(true);
            
            // Set Titles and Badges
            clone.querySelector('.cluster-title').textContent = cluster.theme_name;
            clone.querySelector('.review-count').textContent = `${cluster.review_count} Reviews`;
            
            const badge = clone.querySelector('.badge');
            // Mock logic: If review count is high, mark critical, else moderate
            if (cluster.review_count > 20) {
                badge.classList.add('critical');
                badge.innerHTML = `<i data-lucide="alert-circle" style="width:14px; height:14px;"></i> Critical`;
            } else {
                badge.classList.add('moderate');
                badge.innerHTML = `<i data-lucide="info" style="width:14px; height:14px;"></i> Moderate`;
            }

            // Set Idea and Quote
            clone.querySelector('.idea-text').textContent = cluster.actionable_ideas[0] || "No actionable idea available.";
            clone.querySelector('.quote-text').textContent = `"${cluster.representative_quotes[0] || ""}"`;

            // Setup canvas ID for Chart.js
            const canvas = clone.querySelector('.cluster-chart');
            const canvasId = `chart-${index}`;
            canvas.id = canvasId;

            clustersContainer.appendChild(clone);

            // Need to re-init lucide icons for the newly added elements
            lucide.createIcons();

            // Initialize Chart
            initChart(canvasId, index, cluster);
        });

        // Setup Export Button Listener
        const exportBtn = document.getElementById('btn-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', async () => {
                const originalText = exportBtn.innerHTML;
                exportBtn.innerHTML = '<i data-lucide="loader" class="animate-spin" style="width:16px;height:16px;"></i> Exporting...';
                exportBtn.disabled = true;
                lucide.createIcons();

                try {
                    const reqBody = {
                        content: "Frontend Dashboard Export: Total Reviews processed: " + data.total_reviews_processed,
                        html_content: "<h2>Frontend Export</h2><p>Exported successfully from the frontend dashboard!</p>",
                        subject: "Groww Insights: Dashboard Export"
                    };

                    const response = await fetch('http://127.0.0.1:8003/api/export', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(reqBody)
                    });
                    
                    const result = await response.json();
                    if (response.ok) {
                        alert("Export Successful!\n" + result.doc_status + "\n" + result.email_status);
                    } else {
                        alert("Export Failed: " + (result.detail || "Unknown error"));
                    }
                } catch (err) {
                    console.error("Export error:", err);
                    alert("Export failed to reach backend.");
                } finally {
                    exportBtn.innerHTML = originalText;
                    exportBtn.disabled = false;
                    lucide.createIcons();
                }
            });
        }

        // Setup Sync Button Listener
        const syncBtn = document.getElementById('btn-sync');
        if (syncBtn) {
            syncBtn.addEventListener('click', async () => {
                const originalText = syncBtn.innerHTML;
                syncBtn.innerHTML = '<i data-lucide="loader" class="animate-spin" style="width:16px;height:16px;"></i> Syncing...';
                syncBtn.disabled = true;
                lucide.createIcons();

                try {
                    const response = await fetch('http://127.0.0.1:8003/api/sync', {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        alert("Sync Complete! The dashboard will now refresh with fresh data.");
                        window.location.reload();
                    } else {
                        const result = await response.json();
                        alert("Sync Failed: " + (result.detail || "Unknown error"));
                    }
                } catch (err) {
                    console.error("Sync error:", err);
                    alert("Sync failed to reach backend. Check if bridge is running.");
                } finally {
                    syncBtn.innerHTML = originalText;
                    syncBtn.disabled = false;
                    lucide.createIcons();
                }
            });
        }

        // Tab Switching Logic
        const tabAnalytics = document.getElementById('tab-analytics');
        const tabReports = document.getElementById('tab-reports');
        const viewAnalytics = document.getElementById('analytics-view');
        const viewReports = document.getElementById('reports-view');

        if(tabAnalytics && tabReports) {
            tabAnalytics.addEventListener('click', (e) => {
                e.preventDefault();
                tabAnalytics.classList.add('active');
                tabReports.classList.remove('active');
                viewAnalytics.style.display = 'block';
                viewReports.style.display = 'none';
            });

            tabReports.addEventListener('click', async (e) => {
                e.preventDefault();
                tabReports.classList.add('active');
                tabAnalytics.classList.remove('active');
                viewReports.style.display = 'block';
                viewAnalytics.style.display = 'none';

                const reportsList = document.getElementById('reports-list');
                reportsList.innerHTML = '<p style="color: var(--text-secondary);">Loading reports...</p>';
                
                try {
                    const res = await fetch('http://127.0.0.1:8003/api/reports');
                    const data = await res.json();
                    
                    if (data.history && data.history.length > 0) {
                        reportsList.innerHTML = data.history.map(week => `
                            <div class="report-item">
                                <div class="report-info">
                                    <div class="report-icon">
                                        <i data-lucide="file-check"></i>
                                    </div>
                                    <div>
                                        <div class="report-week">Week: ${week}</div>
                                        <div class="report-status">Status: Processed & Synced</div>
                                    </div>
                                </div>
                                <a href="${data.doc_link}" target="_blank" class="btn-secondary" style="text-decoration: none;">
                                    <i data-lucide="external-link" style="width: 16px; height: 16px;"></i> View Document
                                </a>
                            </div>
                        `).join('');
                    } else {
                        reportsList.innerHTML = '<p style="color: var(--text-secondary);">No reports generated yet.</p>';
                    }
                    lucide.createIcons();
                } catch (err) {
                    reportsList.innerHTML = '<p style="color: var(--accent-red);">Failed to load reports. Is the API Bridge running?</p>';
                }
            });
        }

    } catch (error) {
        console.error("Error loading data:", error);
    }
});

function initChart(canvasId, index, cluster) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Create a gradient for the bar or line
    const gradient = ctx.createLinearGradient(0, 0, 0, 160);
    gradient.addColorStop(0, 'rgba(167, 243, 208, 0.8)'); // Light Green
    gradient.addColorStop(1, 'rgba(52, 211, 153, 0)');    // Transparent Green
    
    // Determine chart type based on index to replicate mockup (0 = Bar, 1 = Line/Area)
    const isBar = index === 0;

    // Mock data based on review count to make charts look somewhat realistic
    const dataPoints = isBar 
        ? [10, 15, 12, 25, 45, 20] 
        : [10, 15, 12, 18, 14, 25, 30, 20];

    new Chart(ctx, {
        type: isBar ? 'bar' : 'line',
        data: {
            labels: dataPoints.map((_, i) => `Day ${i+1}`),
            datasets: [{
                label: 'Volume',
                data: dataPoints,
                backgroundColor: isBar ? gradient : 'rgba(52, 211, 153, 0.1)',
                borderColor: '#34D399',
                borderWidth: isBar ? 0 : 2,
                borderRadius: isBar ? 4 : 0,
                fill: !isBar,
                tension: 0.4, // Smooth curves for line chart
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1E293B',
                    titleColor: '#F8FAFC',
                    bodyColor: '#94A3B8',
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: { display: false },
                y: { display: false, min: 0 }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}
