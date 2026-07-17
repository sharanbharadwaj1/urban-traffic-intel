from fastapi.responses import HTMLResponse


def render_upload_dashboard() -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Surveillance Command Center</title>
        <style>
            :root {
                --paper:#efe7d9; --panel:rgba(255,250,241,.9); --ink:#1b2332; --muted:#617084;
                --border:rgba(27,35,50,.12); --rust:#c2410c; --teal:#0f766e; --warn:#b26b00; --alert:#b42318;
            }
            * { box-sizing:border-box; }
            body {
                margin:0; color:var(--ink); font-family:"Segoe UI", Georgia, serif;
                background:
                    radial-gradient(circle at 15% 10%, rgba(194,65,12,.16), transparent 22%),
                    radial-gradient(circle at 88% 16%, rgba(15,118,110,.14), transparent 24%),
                    linear-gradient(180deg, #f4eee4 0%, #e7decc 100%);
            }
            .shell { max-width:1420px; margin:0 auto; padding:22px; }
            .grid-top, .layout, .stream { display:grid; gap:18px; }
            .grid-top { grid-template-columns:1.6fr 1fr; margin-bottom:18px; }
            .layout { grid-template-columns:360px minmax(0,1fr); }
            .stream { grid-template-columns:1.35fr 1fr; }
            .panel {
                background:var(--panel); border:1px solid var(--border); border-radius:24px; padding:20px;
                box-shadow:0 18px 45px rgba(26,30,43,.08); backdrop-filter:blur(8px);
            }
            .hero h1 { margin:14px 0 8px; font-size:clamp(2.3rem,5vw,4.1rem); line-height:.95; letter-spacing:-.04em; }
            .eyebrow, .badge {
                display:inline-flex; align-items:center; gap:8px; padding:6px 11px; border-radius:999px;
                font-size:.76rem; font-weight:800; text-transform:uppercase; letter-spacing:.08em;
            }
            .eyebrow { background:rgba(27,35,50,.08); color:#24324e; }
            .badge { background:rgba(27,35,50,.08); color:#24324e; }
            .badge.running { background:rgba(15,118,110,.12); color:var(--teal); }
            .badge.completed { background:rgba(10,127,90,.12); color:#0a7f5a; }
            .badge.failed { background:rgba(180,35,24,.12); color:var(--alert); }
            .badge.queued { background:rgba(178,107,0,.12); color:var(--warn); }
            .lead, .subtle { color:var(--muted); line-height:1.5; }
            .status-grid, .metrics, .duo, .trio { display:grid; gap:12px; }
            .status-grid { grid-template-columns:repeat(2, minmax(0,1fr)); margin-top:14px; }
            .metrics { grid-template-columns:repeat(4, minmax(0,1fr)); }
            .duo { grid-template-columns:repeat(2, minmax(0,1fr)); }
            .trio { grid-template-columns:1.2fr 1fr .9fr; }
            .pill, .metric, .card {
                background:rgba(255,255,255,.72); border:1px solid var(--border); border-radius:18px; padding:14px;
            }
            .pill .k, .metric .k { display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }
            .metric .v { font-size:1.95rem; font-weight:800; line-height:1; }
            label { display:block; margin:12px 0 6px; font-weight:700; }
            input, select, button {
                width:100%; padding:12px 14px; border-radius:14px; border:1px solid var(--border);
                font:inherit; background:rgba(255,255,255,.88);
            }
            button {
                margin-top:14px; border:none; color:white; font-weight:700; cursor:pointer;
                background:linear-gradient(135deg, var(--rust), #dc6803);
                box-shadow:0 10px 24px rgba(194,65,12,.2);
            }
            button.secondary { background:linear-gradient(135deg, var(--teal), #0e9384); box-shadow:0 10px 24px rgba(15,118,110,.2); }
            .feed { display:grid; gap:10px; max-height:520px; overflow:auto; }
            .row { display:flex; align-items:center; justify-content:space-between; gap:10px; }
            .progress { margin-top:12px; height:10px; border-radius:999px; background:rgba(27,35,50,.08); overflow:hidden; }
            .progress > span { display:block; height:100%; background:linear-gradient(90deg, var(--teal), var(--rust)); }
            .frame {
                min-height:420px; border-radius:22px; overflow:hidden; position:relative;
                background:linear-gradient(180deg, rgba(23,32,51,.82), rgba(23,32,51,.97));
            }
            .frame img { width:100%; height:100%; object-fit:cover; display:none; }
            .overlay { position:absolute; inset:0; padding:20px; color:#f7f2e9; display:flex; flex-direction:column; justify-content:space-between; }
            .signal { padding:6px 10px; border-radius:999px; font-size:.76rem; font-weight:800; background:rgba(10,127,90,.85); }
            .signal.alert { background:rgba(180,35,24,.85); }
            .meta { display:flex; flex-wrap:wrap; gap:10px; }
            .meta span { padding:8px 10px; border-radius:12px; background:rgba(247,242,233,.12); font-size:.86rem; }
            .gallery { display:grid; grid-template-columns:repeat(auto-fit, minmax(230px,1fr)); gap:14px; }
            .shot { overflow:hidden; border-radius:20px; background:rgba(255,255,255,.8); border:1px solid var(--border); }
            .shot img { width:100%; height:180px; object-fit:cover; display:block; background:#d8d0c1; }
            .shot .info { padding:12px; }
            .empty { padding:22px; border:1px dashed var(--border); border-radius:18px; background:rgba(255,255,255,.4); color:var(--muted); text-align:center; }
            @media (max-width:1180px) { .grid-top, .layout, .stream, .trio { grid-template-columns:1fr; } .metrics, .duo, .status-grid { grid-template-columns:repeat(2, minmax(0,1fr)); } }
            @media (max-width:720px) { .shell { padding:14px; } .metrics, .duo, .status-grid { grid-template-columns:1fr; } }
        </style>
    </head>
    <body>
        <div class="shell">
            <section class="grid-top">
                <div class="panel hero">
                    <span class="eyebrow">Live Surveillance Dashboard</span>
                    <h1>Traffic Command Center</h1>
                    <p class="lead">Launch uploads or RTSP sources, watch worker activity, inspect recent alerts, and review visual event evidence from a single command view.</p>
                </div>
                <div class="panel">
                    <span class="eyebrow">System Status</span>
                    <div class="status-grid">
                        <div class="pill"><span class="k">API Health</span><strong id="health-status">Checking...</strong></div>
                        <div class="pill"><span class="k">Storage</span><strong id="health-storage">-</strong></div>
                        <div class="pill"><span class="k">Plate Detection</span><strong id="health-plate">-</strong></div>
                        <div class="pill"><span class="k">Graph</span><strong id="health-graph">-</strong></div>
                    </div>
                </div>
            </section>

            <section class="layout">
                <aside style="display:grid;gap:18px;">
                    <div class="panel">
                        <h2>Upload Video</h2>
                        <form id="file-form">
                            <label for="camera-id-file">Camera ID</label>
                            <input id="camera-id-file" name="camera_id" value="cam-01" />
                            <label for="video-file">Video File</label>
                            <input id="video-file" name="file" type="file" accept="video/*" />
                            <button type="submit">Launch File Job</button>
                        </form>
                        <p class="subtle">Push recorded footage into the processing queue.</p>
                    </div>
                    <div class="panel">
                        <h2>Register RTSP Stream</h2>
                        <form id="rtsp-form">
                            <label for="camera-id-rtsp">Camera ID</label>
                            <input id="camera-id-rtsp" name="camera_id" value="cam-rtsp-01" />
                            <label for="rtsp-url">RTSP URL</label>
                            <input id="rtsp-url" name="rtsp_url" placeholder="rtsp://user:pass@camera/stream" />
                            <button type="submit" class="secondary">Launch RTSP Job</button>
                        </form>
                        <p class="subtle">Use this for live camera feeds.</p>
                    </div>
                    <div class="panel">
                        <h2>Live Controls</h2>
                        <label for="auto-refresh">Auto Refresh</label>
                        <select id="auto-refresh"><option value="on" selected>On</option><option value="off">Off</option></select>
                        <label for="refresh-ms">Refresh Interval</label>
                        <select id="refresh-ms"><option value="2000">2 seconds</option><option value="4000" selected>4 seconds</option><option value="8000">8 seconds</option></select>
                        <label for="manual-job-id">Focus Job ID</label>
                        <input id="manual-job-id" placeholder="Click a job card or paste an id" />
                        <button id="focus-job-btn" type="button">Focus Job</button>
                    </div>
                </aside>

                <main style="display:grid;gap:18px;">
                    <section class="panel">
                        <h2>Operations Snapshot</h2>
                        <div class="metrics">
                            <div class="metric"><span class="k">Tracked Jobs</span><span class="v" id="metric-jobs">0</span></div>
                            <div class="metric"><span class="k">Running</span><span class="v" id="metric-running">0</span></div>
                            <div class="metric"><span class="k">Recent Alerts</span><span class="v" id="metric-events">0</span></div>
                            <div class="metric"><span class="k">Plates Seen</span><span class="v" id="metric-plates">0</span></div>
                        </div>
                    </section>

                    <section class="stream">
                        <div class="panel">
                            <h2>Live Evidence Feed</h2>
                            <div class="frame">
                                <img id="hero-image" alt="Latest evidence" />
                                <div class="overlay">
                                    <div class="row" style="align-items:flex-start;">
                                        <div>
                                            <span class="eyebrow" style="background:rgba(247,242,233,.12);color:#f7f2e9;">Focused Job Feed</span>
                                            <h2 id="hero-title" style="margin:14px 0 8px;color:#f7f2e9;">Waiting for events...</h2>
                                            <div id="hero-text" class="subtle" style="color:rgba(247,242,233,.82);">Launch a job or focus an existing one to begin the live feed.</div>
                                        </div>
                                        <span id="hero-signal" class="signal">Standby</span>
                                    </div>
                                    <div class="meta">
                                        <span id="hero-job">Job: -</span>
                                        <span id="hero-camera">Camera: -</span>
                                        <span id="hero-event">Event: -</span>
                                        <span id="hero-time">Time: -</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="panel">
                            <h2>Live Job Queue</h2>
                            <div id="jobs-list" class="feed"></div>
                        </div>
                    </section>

                    <section class="trio">
                        <div class="panel">
                            <h2>Recent Alert Feed</h2>
                            <div id="events-list" class="feed"></div>
                        </div>
                        <div class="panel">
                            <h2>Focused Job Detail</h2>
                            <div id="job-detail" class="empty">Select a job to inspect detailed processing state.</div>
                        </div>
                        <div class="panel">
                            <h2>Graph Sightings</h2>
                            <div id="graph-list" class="feed"></div>
                        </div>
                    </section>

                    <section class="panel">
                        <h2>Evidence Gallery</h2>
                        <div id="gallery" class="gallery"></div>
                    </section>
                </main>
            </section>
        </div>

        <script>
            let focusedJobId = "";
            let timer = null;
            const els = {
                healthStatus: document.getElementById("health-status"),
                healthStorage: document.getElementById("health-storage"),
                healthPlate: document.getElementById("health-plate"),
                healthGraph: document.getElementById("health-graph"),
                jobsList: document.getElementById("jobs-list"),
                eventsList: document.getElementById("events-list"),
                graphList: document.getElementById("graph-list"),
                gallery: document.getElementById("gallery"),
                jobDetail: document.getElementById("job-detail"),
                heroImage: document.getElementById("hero-image"),
                heroTitle: document.getElementById("hero-title"),
                heroText: document.getElementById("hero-text"),
                heroSignal: document.getElementById("hero-signal"),
                heroJob: document.getElementById("hero-job"),
                heroCamera: document.getElementById("hero-camera"),
                heroEvent: document.getElementById("hero-event"),
                heroTime: document.getElementById("hero-time"),
                metricJobs: document.getElementById("metric-jobs"),
                metricRunning: document.getElementById("metric-running"),
                metricEvents: document.getElementById("metric-events"),
                metricPlates: document.getElementById("metric-plates"),
                manualJobId: document.getElementById("manual-job-id"),
                autoRefresh: document.getElementById("auto-refresh"),
                refreshMs: document.getElementById("refresh-ms")
            };

            function esc(v) {
                return String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
            }
            function fmtDate(v) {
                if (!v) return "-";
                const d = new Date(v);
                return Number.isNaN(d.getTime()) ? v : d.toLocaleString();
            }
            async function safeFetchJson(url, options) {
                const res = await fetch(url, options);
                const text = await res.text();
                let payload;
                try { payload = JSON.parse(text); } catch { payload = { raw: text }; }
                if (!res.ok) throw new Error(payload.detail || payload.raw || res.statusText);
                return payload;
            }
            function setFocus(jobId) {
                focusedJobId = jobId || "";
                els.manualJobId.value = focusedJobId;
            }
            function setHero(event, liveState) {
                if (liveState && liveState.image_url) {
                    els.heroImage.src = `${liveState.image_url}?t=${encodeURIComponent(liveState.updated_at || Date.now())}`;
                    els.heroImage.style.display = "block";
                    els.heroTitle.textContent = `Frame ${liveState.frame_index}`;
                    els.heroText.textContent = `${(liveState.tracked_objects || []).length} tracked objects in the active surveillance frame.`;
                    els.heroSignal.textContent = (liveState.alerts || []).length ? "Alert" : "Live";
                    els.heroSignal.className = (liveState.alerts || []).length ? "signal alert" : "signal";
                    els.heroJob.textContent = `Job: ${liveState.job_id}`;
                    els.heroCamera.textContent = `Camera: ${liveState.camera_id || "-"}`;
                    els.heroEvent.textContent = `Alerts: ${(liveState.alerts || []).map(item => item.event_type).join(", ") || "none"}`;
                    els.heroTime.textContent = `Updated: ${fmtDate(liveState.updated_at)}`;
                    return;
                }
                if (!event) {
                    els.heroImage.style.display = "none";
                    els.heroImage.removeAttribute("src");
                    els.heroTitle.textContent = "Waiting for events...";
                    els.heroText.textContent = "Launch a job or focus an existing one to begin the live feed.";
                    els.heroSignal.textContent = "Standby";
                    els.heroSignal.className = "signal";
                    els.heroJob.textContent = "Job: -";
                    els.heroCamera.textContent = "Camera: -";
                    els.heroEvent.textContent = "Event: -";
                    els.heroTime.textContent = "Time: -";
                    return;
                }
                const snapshot = event.metadata && event.metadata.snapshot_url;
                if (snapshot && !snapshot.startsWith("s3://")) {
                    els.heroImage.src = snapshot;
                    els.heroImage.style.display = "block";
                } else {
                    els.heroImage.style.display = "none";
                    els.heroImage.removeAttribute("src");
                }
                els.heroTitle.textContent = event.event_type;
                els.heroText.textContent = `${event.class_name || "Object"} detected with confidence ${event.confidence ?? "-"}. Plate ${event.plate || "pending confirmation"}.`;
                els.heroSignal.textContent = (event.event_type || "").includes("stationary") ? "Alert" : "Active";
                els.heroSignal.className = (event.event_type || "").includes("stationary") ? "signal alert" : "signal";
                els.heroJob.textContent = `Job: ${event.job_id}`;
                els.heroCamera.textContent = `Camera: ${event.camera_id}`;
                els.heroEvent.textContent = `Event: ${event.event_type}`;
                els.heroTime.textContent = `Time: ${fmtDate(event.event_timestamp)}`;
            }
            function renderHealth(health) {
                els.healthStatus.textContent = health.status;
                els.healthStorage.textContent = health.storage_backend;
                els.healthPlate.textContent = health.plate_detection_enabled ? "Enabled" : "Disabled";
                els.healthGraph.textContent = health.graph_enabled ? "Enabled" : "Disabled";
            }
            function renderJobs(jobs) {
                els.metricJobs.textContent = jobs.length;
                els.metricRunning.textContent = jobs.filter(j => j.status === "running").length;
                if (!focusedJobId && jobs.length) setFocus(jobs[0].job_id);
                if (!jobs.length) {
                    els.jobsList.innerHTML = '<div class="empty">No jobs yet. Submit a video or RTSP stream to begin.</div>';
                    return;
                }
                els.jobsList.innerHTML = jobs.map(job => {
                    const pct = job.total_frames > 0 ? Math.min(100, Math.round((job.processed_frames / job.total_frames) * 100)) : 0;
                    return `
                        <div class="card" data-job-id="${esc(job.job_id)}" style="${job.job_id===focusedJobId?'border-color:rgba(15,118,110,.35);box-shadow:inset 0 0 0 1px rgba(15,118,110,.12);':''}">
                            <div class="row">
                                <div>
                                    <div style="font-weight:800;">${esc(job.camera_id)}</div>
                                    <div class="subtle">${esc(job.source_type)} · ${esc(job.job_id.slice(0, 12))}</div>
                                </div>
                                <span class="badge ${esc(job.status)}">${esc(job.status)}</span>
                            </div>
                            <div class="subtle" style="margin-top:10px;">Frames ${job.processed_frames}/${job.total_frames || "?"} · ${esc(fmtDate(job.created_at))}</div>
                            <div class="progress"><span style="width:${pct}%"></span></div>
                        </div>
                    `;
                }).join("");
                for (const node of els.jobsList.querySelectorAll("[data-job-id]")) {
                    node.addEventListener("click", async () => { setFocus(node.dataset.jobId); await refreshDashboard(); });
                }
            }
            function renderJobDetail(job) {
                if (!job) {
                    els.jobDetail.className = "empty";
                    els.jobDetail.textContent = "Select a job to inspect detailed processing state.";
                    return;
                }
                const pct = job.total_frames > 0 ? Math.min(100, Math.round((job.processed_frames / job.total_frames) * 100)) : 0;
                els.jobDetail.className = "card";
                els.jobDetail.innerHTML = `
                    <div class="row">
                        <div style="font-weight:800;">${esc(job.camera_id)}</div>
                        <span class="badge ${esc(job.status)}">${esc(job.status)}</span>
                    </div>
                    <div class="subtle" style="margin-top:12px;">Job ${esc(job.job_id)}</div>
                    <div class="subtle">Queue ${esc(job.queue_task_id || "-")}</div>
                    <div class="subtle">Source ${esc(job.source_type)}</div>
                    <div class="subtle">Frames ${esc(job.processed_frames)} / ${esc(job.total_frames)}</div>
                    <div class="subtle">Created ${esc(fmtDate(job.created_at))}</div>
                    <div class="subtle">Completed ${esc(fmtDate(job.completed_at))}</div>
                    <div class="progress"><span style="width:${pct}%"></span></div>
                    <div class="subtle" style="margin-top:12px;">${esc(job.error_message || "No worker error reported.")}</div>
                `;
            }
            function renderEvents(events) {
                els.metricEvents.textContent = events.length;
                els.metricPlates.textContent = new Set(events.map(e => e.plate).filter(Boolean)).size;
                if (!events.length) {
                    els.eventsList.innerHTML = '<div class="empty">No recent events for the focused job yet.</div>';
                    els.gallery.innerHTML = '<div class="empty">Event snapshots will appear here once detections are stored.</div>';
                    setHero(null);
                    return;
                }
                els.eventsList.innerHTML = events.map(event => `
                    <div class="card">
                        <div class="row">
                            <div style="font-weight:800;">${esc(event.event_type)}</div>
                            <span class="badge ${(event.event_type || "").includes("stationary") ? "failed" : "running"}">${esc(event.class_name || "unknown")}</span>
                        </div>
                        <div class="subtle" style="margin-top:8px;">Camera ${esc(event.camera_id)} · Track ${esc(event.track_id ?? "-")} · Plate ${esc(event.plate || "-")}</div>
                        <div class="subtle">${esc(fmtDate(event.event_timestamp))}</div>
                    </div>
                `).join("");
                const shots = events.filter(e => e.metadata && e.metadata.snapshot_url).slice(0, 6);
                if (!shots.length) {
                    els.gallery.innerHTML = '<div class="empty">Recent events exist, but no visual snapshot was stored for them.</div>';
                } else {
                    els.gallery.innerHTML = shots.map(event => `
                        <article class="shot">
                            <img src="${esc(event.metadata.snapshot_url)}" alt="${esc(event.event_type)}" />
                            <div class="info">
                                <strong>${esc(event.event_type)}</strong>
                                <div class="subtle">Camera ${esc(event.camera_id)} · Track ${esc(event.track_id ?? "-")}</div>
                                <div class="subtle">Plate ${esc(event.plate || "-")} · ${esc(fmtDate(event.event_timestamp))}</div>
                            </div>
                        </article>
                    `).join("");
                }
                setHero(shots[0] || events[0], null);
            }
            function renderGraphSightings(items) {
                if (!items.length) {
                    els.graphList.innerHTML = '<div class="empty">No graph sightings available for the focused camera yet.</div>';
                    return;
                }
                els.graphList.innerHTML = items.map(item => `
                    <div class="card">
                        <div class="row">
                            <div style="font-weight:800;">${esc(item.plate)}</div>
                            <span class="badge completed">${esc(item.camera_id)}</span>
                        </div>
                        <div class="subtle" style="margin-top:8px;">First seen ${esc(item.first_seen_at)}</div>
                        <div class="subtle">Last seen ${esc(item.last_seen_at)}</div>
                        <div class="subtle">Sightings ${esc(item.total_sightings)}</div>
                    </div>
                `).join("");
            }
            async function submitFileJob(event) {
                event.preventDefault();
                const payload = await safeFetchJson("/upload-video", { method:"POST", body:new FormData(document.getElementById("file-form")) });
                setFocus(payload.job_id);
                await refreshDashboard();
            }
            async function submitRtspJob(event) {
                event.preventDefault();
                const payload = await safeFetchJson("/upload-video", { method:"POST", body:new FormData(document.getElementById("rtsp-form")) });
                setFocus(payload.job_id);
                await refreshDashboard();
            }
            async function refreshDashboard() {
                try {
                    const [health, jobsPayload] = await Promise.all([safeFetchJson("/health"), safeFetchJson("/jobs?limit=12")]);
                    renderHealth(health);
                    renderJobs(jobsPayload.items || []);
                    let job = null;
                    let liveState = null;
                    if (focusedJobId) {
                        job = await safeFetchJson(`/jobs/${encodeURIComponent(focusedJobId)}`);
                        try {
                            liveState = await safeFetchJson(`/jobs/${encodeURIComponent(focusedJobId)}/live-state`);
                        } catch {}
                    }
                    renderJobDetail(job);
                    const eventsPayload = await safeFetchJson(focusedJobId ? `/events?job_id=${encodeURIComponent(focusedJobId)}&limit=12` : "/events?limit=12");
                    renderEvents(eventsPayload.items || []);
                    if (job && job.camera_id) {
                        try {
                            const graphPayload = await safeFetchJson(`/graph/sightings?camera_id=${encodeURIComponent(job.camera_id)}&limit=10`);
                            renderGraphSightings(graphPayload.items || []);
                        } catch {
                            renderGraphSightings([]);
                        }
                    } else {
                        renderGraphSightings([]);
                    }
                    if (liveState) {
                        setHero(null, liveState);
                    }
                } catch (error) {
                    els.eventsList.innerHTML = `<div class="empty">Dashboard refresh failed: ${esc(error.message)}</div>`;
                }
            }
            function reschedule() {
                if (timer) clearInterval(timer);
                if (els.autoRefresh.value === "on") timer = setInterval(refreshDashboard, Number(els.refreshMs.value));
            }
            document.getElementById("file-form").addEventListener("submit", submitFileJob);
            document.getElementById("rtsp-form").addEventListener("submit", submitRtspJob);
            document.getElementById("focus-job-btn").addEventListener("click", async () => { setFocus(els.manualJobId.value.trim()); await refreshDashboard(); });
            els.autoRefresh.addEventListener("change", reschedule);
            els.refreshMs.addEventListener("change", reschedule);
            refreshDashboard();
            reschedule();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
