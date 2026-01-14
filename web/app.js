/**
 * VP-CORE Frontend Application
 * Vanilla JavaScript with API integration
 */

// === Configuration ===
const API_BASE = 'http://127.0.0.1:8000';
const POLL_INTERVAL = 1000; // 1 second

// === State ===
let currentPage = 'search';
let searchResults = [];
let tasks = [];
let stats = {};
let pollTimer = null;

// === API Client ===
const api = {
    async search(query, maxResults = 20) {
        const params = new URLSearchParams({
            query,
            max_results: maxResults,
            duration_min: 60,
            duration_max: 3600
        });
        const res = await fetch(`${API_BASE}/api/search?${params}`, { method: 'POST' });
        if (!res.ok) throw new Error('Search failed');
        return res.json();
    },

    async createTask(url) {
        const res = await fetch(`${API_BASE}/api/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!res.ok) throw new Error('Failed to create task');
        return res.json();
    },

    async getTasks() {
        const res = await fetch(`${API_BASE}/api/tasks`);
        if (!res.ok) throw new Error('Failed to get tasks');
        return res.json();
    },

    async deleteTask(taskId) {
        const res = await fetch(`${API_BASE}/api/tasks/${taskId}`, { method: 'DELETE' });
        return res.json();
    },

    async getStats() {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (!res.ok) throw new Error('Failed to get stats');
        return res.json();
    },

    async shutdown() {
        await fetch(`${API_BASE}/api/shutdown`, { method: 'POST' });
    },

    async startAll() {
        const res = await fetch(`${API_BASE}/api/tasks/start-all`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to start tasks');
        return res.json();
    }
};

// === Utility Functions ===
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function getStageClass(stage, currentStage, stageProgress) {
    if (stage < currentStage) return 'bg-primary'; // Completed
    if (stage === currentStage) return 'bg-primary/20'; // Active
    return 'bg-slate-800'; // Pending
}

// === Page Renderers ===

function renderSearchPage() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div class="flex items-center gap-2">
                <h2 class="text-2xl font-bold mr-4">Results</h2>
                <span id="result-count" class="text-slate-500 text-sm"></span>
            </div>
            <div class="flex items-center gap-2 bg-slate-100 dark:bg-surface p-1 rounded-lg border border-border-subtle">
                <button class="p-1.5 rounded bg-white dark:bg-border-subtle text-primary">
                    <span class="material-symbols-outlined text-[20px]">grid_view</span>
                </button>
                <button class="p-1.5 rounded text-slate-400 hover:text-white">
                    <span class="material-symbols-outlined text-[20px]">view_list</span>
                </button>
            </div>
        </div>
        
        <div class="flex gap-8 flex-col xl:flex-row">
            <!-- Video Grid -->
            <div class="flex-1">
                <div id="video-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div class="text-center text-slate-500 col-span-full py-16">
                        <span class="material-symbols-outlined text-6xl mb-4 block">search</span>
                        <p>Search for videos to get started</p>
                    </div>
                </div>
            </div>
            
            <!-- Task Sidebar -->
            <aside class="w-full xl:w-[380px] shrink-0">
                <div id="task-sidebar" class="bg-slate-50 dark:bg-surface border border-border-subtle rounded-xl overflow-hidden sticky top-24">
                    <div class="p-5 border-b border-border-subtle flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">assignment</span>
                            <h3 class="font-bold">Active Tasks</h3>
                        </div>
                        <span id="sidebar-task-count" class="bg-primary/20 text-primary px-2 py-0.5 rounded text-xs font-bold">0</span>
                    </div>
                    <div id="sidebar-tasks" class="p-5 flex flex-col gap-4 max-h-[500px] overflow-y-auto custom-scrollbar">
                        <p class="text-slate-500 text-sm text-center py-4">No active tasks</p>
                    </div>
                    <div class="p-5 bg-slate-100 dark:bg-background-dark/50 border-t border-border-subtle">
                        <button id="process-all-btn" class="w-full py-3 bg-primary text-background-dark font-bold rounded-lg text-sm hover:brightness-110 flex items-center justify-center gap-2 disabled:opacity-50" disabled>
                            <span class="material-symbols-outlined">play_arrow</span>
                            PROCESS ALL TASKS
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    `;
}

function renderTasksPage() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="flex flex-col mb-8">
            <p class="text-slate-500 text-sm font-medium">Pipeline Management</p>
            <h3 class="text-3xl font-bold tracking-tight">Active Processing Jobs</h3>
        </div>
        
        <!-- Tabs -->
        <div class="flex border-b border-border-subtle gap-8 mb-8">
            <a class="border-b-2 border-primary text-primary pb-4 px-1 text-sm font-bold">Processing (<span id="processing-count">0</span>)</a>
            <a class="border-b-2 border-transparent text-slate-500 pb-4 px-1 text-sm font-bold">Queued (<span id="queued-count">0</span>)</a>
            <a class="border-b-2 border-transparent text-slate-500 pb-4 px-1 text-sm font-bold">Completed (<span id="completed-count">0</span>)</a>
        </div>
        
        <!-- Task List -->
        <div id="task-list" class="grid gap-4">
            <p class="text-slate-500 text-center py-8">No tasks yet. Search and add videos to process.</p>
        </div>
        
        <!-- Stats Footer -->
        <div id="stats-footer" class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-slate-100 dark:bg-slate-900/50 p-4 rounded-lg border border-border-subtle flex justify-between items-center">
                <div>
                    <p class="text-[10px] font-bold text-slate-500 uppercase">CPU Usage</p>
                    <p id="stat-cpu" class="text-lg font-bold">0%</p>
                </div>
                <span class="material-symbols-outlined text-primary">speed</span>
            </div>
            <div class="bg-slate-100 dark:bg-slate-900/50 p-4 rounded-lg border border-border-subtle flex justify-between items-center">
                <div>
                    <p class="text-[10px] font-bold text-slate-500 uppercase">Storage Available</p>
                    <p id="stat-storage" class="text-lg font-bold">N/A</p>
                </div>
                <span class="material-symbols-outlined text-primary">storage</span>
            </div>
            <div class="bg-slate-100 dark:bg-slate-900/50 p-4 rounded-lg border border-border-subtle flex justify-between items-center">
                <div>
                    <p class="text-[10px] font-bold text-slate-500 uppercase">System Uptime</p>
                    <p id="stat-uptime" class="text-lg font-bold">0m</p>
                </div>
                <span class="material-symbols-outlined text-primary">terminal</span>
            </div>
        </div>
    `;
}

// === Component Renderers ===

function renderVideoCard(video) {
    return `
        <div class="video-card group flex flex-col bg-slate-50 dark:bg-surface border border-border-subtle rounded-xl overflow-hidden transition-all duration-300">
            <div class="relative aspect-video overflow-hidden cursor-pointer" onclick="openVideoModal('${video.id}')">
                <div class="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity z-10 flex items-center justify-center pointer-events-none">
                    <span class="material-symbols-outlined text-primary text-5xl transform scale-75 group-hover:scale-100 transition-transform">play_circle</span>
                </div>
                <img alt="${video.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src="${video.thumbnail_url}" onerror="this.src='https://via.placeholder.com/320x180?text=No+Image'">
                <span class="absolute bottom-2 right-2 bg-black/80 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">${video.duration_str}</span>
            </div>
            <div class="p-4 flex flex-col flex-1">
                <h3 class="text-base font-bold leading-tight mb-2 group-hover:text-primary transition-colors line-clamp-2">${video.title}</h3>
                <div class="flex flex-col gap-1 mb-4">
                    <p class="text-slate-400 text-xs flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">account_circle</span>
                        ${video.channel} • ${video.view_count_str}
                    </p>
                    <p class="text-slate-400 text-xs flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">history</span>
                        ${video.upload_date}
                    </p>
                </div>
                <div class="mt-auto grid grid-cols-2 gap-2">
                    <button onclick="openVideoModal('${video.id}')" class="flex items-center justify-center gap-2 py-2 rounded-lg border border-primary/40 text-primary text-xs font-bold hover:bg-primary/5">
                        <span class="material-symbols-outlined text-[16px]">visibility</span>
                        PREVIEW
                    </button>
                    <button onclick="addTask('${video.url}')" class="flex items-center justify-center gap-2 py-2 rounded-lg bg-primary text-background-dark text-xs font-bold hover:brightness-110 shadow-md">
                        <span class="material-symbols-outlined text-[16px]">add_task</span>
                        ADD TASK
                    </button>
                </div>
            </div>
        </div>
    `;
}

function renderTaskCard(task) {
    const stages = ['START', 'DOWNLOAD', 'SUBTITLES', 'ENCODING', 'FINISHED'];
    const stageIndex = task.stage;

    return `
        <div class="bg-white dark:bg-[#1e1e1e] border border-border-subtle p-5 rounded-xl hover:border-primary/50 transition-all">
            <div class="flex flex-col md:flex-row gap-6 items-start md:items-center">
                <div class="relative shrink-0">
                    <div class="w-40 h-24 rounded-lg bg-cover bg-center border border-border-subtle" style="background-image: url('${task.thumbnail_url}')"></div>
                    <div class="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1.5 py-0.5 rounded font-bold">${task.duration_str || '0:00'}</div>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="text-lg font-bold truncate pr-4">${task.title || 'Processing...'}</h4>
                        <div class="flex gap-2 shrink-0">
                            <span class="material-symbols-outlined text-slate-400 cursor-pointer hover:text-red-500" onclick="deleteTask('${task.task_id}')">close</span>
                        </div>
                    </div>
                    <!-- 5-Stage Progress Bar -->
                    <div class="grid grid-cols-5 gap-1.5 mt-4">
                        ${stages.map((name, i) => {
        const stageNum = i + 1;
        const isCompleted = stageNum < stageIndex;
        const isActive = stageNum === stageIndex;
        const bgClass = isCompleted ? 'bg-primary' : (isActive ? 'bg-primary/20' : 'bg-slate-800');
        const textClass = isCompleted || isActive ? 'text-primary' : 'text-slate-500';

        return `
                                <div class="relative h-10 flex flex-col justify-center items-center">
                                    <div class="w-full h-2 ${bgClass} rounded-sm stage-segment overflow-hidden">
                                        ${isActive ? `<div class="h-full bg-primary" style="width: ${task.stage_progress}%"></div>` : ''}
                                    </div>
                                    <span class="text-[9px] font-bold uppercase mt-2 ${textClass} tracking-widest flex items-center gap-1">
                                        ${isActive ? '<span class="block w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>' : ''}
                                        ${name}
                                    </span>
                                </div>
                            `;
    }).join('')}
                    </div>
                </div>
                <div class="shrink-0 flex flex-col items-end gap-1 px-4">
                    <span class="text-3xl font-bold ${task.status === 'completed' ? 'text-green-500' : task.status === 'failed' ? 'text-red-500' : 'text-primary'}">${Math.round(task.overall_progress)}%</span>
                    <span class="text-[10px] font-bold text-slate-500 uppercase">${task.message}</span>
                </div>
            </div>
        </div>
    `;
}

function renderSidebarTask(task) {
    return `
        <div class="flex flex-col gap-2">
            <div class="flex gap-3">
                <div class="w-16 h-10 bg-border-subtle rounded overflow-hidden shrink-0">
                    <img src="${task.thumbnail_url}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/64x40'">
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-xs font-bold truncate">${task.title || 'Processing...'}</p>
                    <p class="text-[10px] text-slate-400 uppercase">${task.stage_name}</p>
                </div>
                <button onclick="deleteTask('${task.task_id}')" class="text-slate-400 hover:text-red-500">
                    <span class="material-symbols-outlined text-[16px]">close</span>
                </button>
            </div>
            <div class="w-full bg-background-dark h-1.5 rounded-full overflow-hidden">
                <div class="bg-primary h-full transition-all" style="width: ${task.overall_progress}%"></div>
            </div>
            <div class="flex justify-between text-[10px]">
                <span class="text-slate-400">${task.message}</span>
                <span class="text-primary font-bold">${Math.round(task.overall_progress)}%</span>
            </div>
        </div>
    `;
}

// === Actions ===

async function doSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    const grid = document.getElementById('video-grid');
    grid.innerHTML = '<div class="loading-spinner mx-auto"></div>';

    try {
        const data = await api.search(query);
        searchResults = data.items;
        document.getElementById('result-count').textContent = `${data.total} results`;

        if (searchResults.length === 0) {
            grid.innerHTML = '<p class="text-slate-500 text-center col-span-full py-8">No videos found</p>';
        } else {
            grid.innerHTML = searchResults.map(renderVideoCard).join('');
        }
    } catch (e) {
        grid.innerHTML = `<p class="text-red-500 text-center col-span-full py-8">Error: ${e.message}</p>`;
    }
}

async function addTask(url) {
    try {
        console.log('[VP-CORE] Adding task:', url);
        const task = await api.createTask(url);
        tasks.push(task);
        updateTaskBadge();
        updateSidebar();
        console.log('[VP-CORE] Task added successfully:', task.task_id);
        // No alert - just update UI silently
    } catch (e) {
        console.error('[VP-CORE] Failed to add task:', e);
        alert('Failed to add task: ' + e.message);
    }
}

async function deleteTask(taskId) {
    try {
        await api.deleteTask(taskId);
        tasks = tasks.filter(t => t.task_id !== taskId);
        updateUI();
    } catch (e) {
        console.error('Failed to delete task:', e);
    }
}

function openVideoModal(videoId) {
    const video = searchResults.find(v => v.id === videoId);
    if (!video) return;

    const modal = document.getElementById('video-modal');
    modal.innerHTML = `
        <div class="relative w-full max-w-4xl bg-surface rounded-2xl overflow-hidden shadow-2xl">
            <button onclick="closeVideoModal()" class="absolute top-4 right-4 z-50 p-2 bg-black/40 hover:bg-black/60 text-white rounded-full">
                <span class="material-symbols-outlined">close</span>
            </button>
            <div class="aspect-video bg-black flex items-center justify-center">
                <img src="${video.thumbnail_url}" class="w-full h-full object-cover opacity-60">
                <div class="absolute inset-0 flex items-center justify-center">
                    <a href="${video.url}" target="_blank" class="w-20 h-20 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center hover:scale-110 transition-transform">
                        <span class="material-symbols-outlined text-primary text-5xl">play_arrow</span>
                    </a>
                </div>
            </div>
            <div class="p-6">
                <h2 class="text-xl font-bold mb-2">${video.title}</h2>
                <p class="text-slate-400 mb-4">${video.channel} • ${video.view_count_str}</p>
                <button onclick="addTask('${video.url}'); closeVideoModal();" class="w-full py-4 bg-primary text-background-dark font-bold rounded-xl flex items-center justify-center gap-2 hover:brightness-110">
                    <span class="material-symbols-outlined">add_task</span>
                    ADD TO TASK QUEUE
                </button>
            </div>
        </div>
    `;
    modal.classList.remove('hidden');
}

function closeVideoModal() {
    document.getElementById('video-modal').classList.add('hidden');
}

// === Update Functions ===

async function pollTasks() {
    try {
        tasks = await api.getTasks();
        stats = await api.getStats();
        updateUI();
    } catch (e) {
        console.error('Poll error:', e);
    }
}

function updateUI() {
    updateTaskBadge();
    updateSidebar();

    if (currentPage === 'tasks') {
        updateTasksPage();
    }
}

function updateTaskBadge() {
    const active = tasks.filter(t => t.status === 'running' || t.status === 'pending').length;
    const badge = document.getElementById('task-badge');
    if (active > 0) {
        badge.textContent = active;
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

function updateSidebar() {
    const container = document.getElementById('sidebar-tasks');
    const countEl = document.getElementById('sidebar-task-count');
    const btn = document.getElementById('process-all-btn');

    if (!container) return;

    const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending');
    countEl.textContent = activeTasks.length;

    if (activeTasks.length === 0) {
        container.innerHTML = '<p class="text-slate-500 text-sm text-center py-4">No active tasks</p>';
        if (btn) btn.disabled = true;
    } else {
        container.innerHTML = activeTasks.map(renderSidebarTask).join('<hr class="border-border-subtle">');
        // Only enable if there are pending (not running) tasks
        const pendingTasks = tasks.filter(t => t.status === 'pending');
        if (btn) btn.disabled = pendingTasks.length === 0;
    }
}

function updateTasksPage() {
    const processing = tasks.filter(t => t.status === 'running').length;
    const queued = tasks.filter(t => t.status === 'pending').length;
    const completed = tasks.filter(t => t.status === 'completed').length;

    const processingEl = document.getElementById('processing-count');
    const queuedEl = document.getElementById('queued-count');
    const completedEl = document.getElementById('completed-count');

    if (processingEl) processingEl.textContent = processing;
    if (queuedEl) queuedEl.textContent = queued;
    if (completedEl) completedEl.textContent = completed;

    const taskList = document.getElementById('task-list');
    if (!taskList) return;

    // Show all tasks, not just active ones
    const allTasks = tasks;

    if (allTasks.length === 0) {
        taskList.innerHTML = '<p class="text-slate-500 text-center py-8">No tasks yet.</p>';
    } else {
        taskList.innerHTML = allTasks.map(renderTaskCard).join('');
    }

    // Update stats with null-safe access
    const cpuEl = document.getElementById('stat-cpu');
    const storageEl = document.getElementById('stat-storage');
    const uptimeEl = document.getElementById('stat-uptime');

    if (cpuEl) cpuEl.textContent = `${stats.cpu_usage || 0}%`;
    if (storageEl) storageEl.textContent = stats.storage_available || 'N/A';
    if (uptimeEl) uptimeEl.textContent = stats.uptime || '0m';
}

// === Navigation ===

function navigateTo(page) {
    currentPage = page;

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('text-primary', link.dataset.page === page);
    });

    // Render page
    if (page === 'search') {
        renderSearchPage();
    } else if (page === 'tasks') {
        renderTasksPage();
        updateTasksPage();
    }
}

// === Initialization ===

document.addEventListener('DOMContentLoaded', () => {
    // Setup navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(link.dataset.page);
        });
    });

    // Setup search
    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    });

    // Setup exit
    document.getElementById('exit-btn').addEventListener('click', async () => {
        if (confirm('Shutdown the server?')) {
            await api.shutdown();
            window.close();
        }
    });

    // Initial render
    navigateTo('search');

    // Start polling
    pollTimer = setInterval(pollTasks, POLL_INTERVAL);
    pollTasks();

    // Setup process all btn handler after page renders
    setupProcessAllBtn();
});

// Setup process all button
function setupProcessAllBtn() {
    setTimeout(() => {
        const btn = document.getElementById('process-all-btn');
        if (btn) {
            btn.onclick = async () => {
                try {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="loading-spinner"></span> Starting...';
                    await api.startAll();
                    await pollTasks();
                    btn.innerHTML = '<span class="material-symbols-outlined">play_arrow</span> PROCESS ALL TASKS';
                } catch (e) {
                    alert('Failed to start tasks: ' + e.message);
                    btn.disabled = false;
                    btn.innerHTML = '<span class="material-symbols-outlined">play_arrow</span> PROCESS ALL TASKS';
                }
            };
        }
    }, 100);
}

// Make functions available globally
window.addTask = addTask;
window.deleteTask = deleteTask;
window.openVideoModal = openVideoModal;
window.closeVideoModal = closeVideoModal;
