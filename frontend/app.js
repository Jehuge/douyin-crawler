// API 基础 URL
const API_BASE = '';

// 状态更新
let statusCheckInterval = null;

// DOM 元素
const elements = {
    crawlerType: document.getElementById('crawler-type'),
    keywordsGroup: document.getElementById('keywords-group'),
    videoUrlsGroup: document.getElementById('video-urls-group'),
    creatorUrlsGroup: document.getElementById('creator-urls-group'),
    keywords: document.getElementById('keywords'),
    videoUrls: document.getElementById('video-urls'),
    creatorUrls: document.getElementById('creator-urls'),
    maxCount: document.getElementById('max-count'),
    enableMedia: document.getElementById('enable-media'),
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    clearBtn: document.getElementById('clear-btn'),
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    videoCount: document.getElementById('video-count'),
    creatorCount: document.getElementById('creator-count'),
    videosTbody: document.getElementById('videos-tbody'),
    creatorsTbody: document.getElementById('creators-tbody')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadData();
    startStatusCheck();
});

// 事件监听
function initEventListeners() {
    // 爬取模式切换
    elements.crawlerType.addEventListener('change', () => {
        const type = elements.crawlerType.value;
        elements.keywordsGroup.classList.toggle('hidden', type !== 'search');
        elements.videoUrlsGroup.classList.toggle('hidden', type !== 'detail');
        elements.creatorUrlsGroup.classList.toggle('hidden', type !== 'creator');
    });

    // 按钮事件
    elements.startBtn.addEventListener('click', startCrawler);
    elements.stopBtn.addEventListener('click', stopCrawler);
    elements.clearBtn.addEventListener('click', clearData);

    // 标签切换
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
}

// 开始爬取
async function startCrawler() {
    const type = elements.crawlerType.value;
    const config = {
        crawler_type: type,
        max_count: parseInt(elements.maxCount.value),
        enable_media: elements.enableMedia.checked
    };

    if (type === 'search') {
        config.keywords = elements.keywords.value.trim();
        if (!config.keywords) {
            alert('请输入搜索关键词');
            return;
        }
    } else if (type === 'detail') {
        const urls = elements.videoUrls.value.trim();
        if (!urls) {
            alert('请输入视频URL');
            return;
        }
        config.video_urls = urls.split('\n').filter(u => u.trim()).map(u => u.trim());
        console.log('发送视频URL:', config.video_urls);
    } else if (type === 'creator') {
        const urls = elements.creatorUrls.value.trim();
        if (!urls) {
            alert('请输入创作者URL');
            return;
        }
        config.creator_urls = urls.split('\n').filter(u => u.trim()).map(u => u.trim());
        console.log('发送创作者URL:', config.creator_urls);
    }

    console.log('爬虫配置:', config);

    try {
        const response = await fetch(`${API_BASE}/api/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (response.ok) {
            updateStatus('running', '爬取中...');
            elements.startBtn.disabled = true;
            elements.stopBtn.disabled = false;
            alert(`爬虫已启动！模式: ${type}`);
        } else {
            alert(data.detail || '启动失败');
        }
    } catch (error) {
        console.error('启动失败:', error);
        alert('启动失败: ' + error.message);
    }
}

// 停止爬取
async function stopCrawler() {
    try {
        const response = await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            updateStatus('idle', '已停止');
            elements.startBtn.disabled = false;
            elements.stopBtn.disabled = true;
        }
    } catch (error) {
        console.error('停止失败:', error);
    }
}

// 清空数据
async function clearData() {
    if (!confirm('确定要清空所有数据吗？')) return;

    try {
        const response = await fetch(`${API_BASE}/api/videos/clear`, { method: 'DELETE' });

        if (response.ok) {
            loadData();
            alert('数据已清空');
        }
    } catch (error) {
        console.error('清空失败:', error);
        alert('清空失败');
    }
}

// 加载数据
async function loadData() {
    await Promise.all([
        loadVideos(),
        loadCreators(),
        loadCounts()
    ]);
}

// 加载视频列表
async function loadVideos() {
    try {
        const response = await fetch(`${API_BASE}/api/videos?limit=100`);
        const videos = await response.json();

        if (videos.length === 0) {
            elements.videosTbody.innerHTML = '<tr><td colspan="5" class="no-data">暂无数据</td></tr>';
            return;
        }

        elements.videosTbody.innerHTML = videos.map(v => `
            <tr>
                <td>${escapeHtml(v.title || '无标题')}</td>
                <td>${escapeHtml(v.author_name || '-')}</td>
                <td>${formatNumber(v.like_count)}</td>
                <td>${escapeHtml(v.keyword || '-')}</td>
                <td>
                    <button class="btn-link" onclick="window.open('${v.video_url}', '_blank')">查看</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载视频失败:', error);
    }
}

// 加载创作者列表
async function loadCreators() {
    try {
        const response = await fetch(`${API_BASE}/api/creators?limit=100`);
        const creators = await response.json();

        if (creators.length === 0) {
            elements.creatorsTbody.innerHTML = '<tr><td colspan="4" class="no-data">暂无数据</td></tr>';
            return;
        }

        elements.creatorsTbody.innerHTML = creators.map(c => `
            <tr>
                <td>${escapeHtml(c.nickname || '-')}</td>
                <td>${formatNumber(c.follower_count)}</td>
                <td>${formatNumber(c.aweme_count)}</td>
                <td><code>${c.sec_user_id.substring(0, 20)}...</code></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('加载创作者失败:', error);
    }
}

// 加载统计数据
async function loadCounts() {
    try {
        const response = await fetch(`${API_BASE}/api/videos/count`);
        const data = await response.json();
        elements.videoCount.textContent = data.count;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 切换标签
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// 状态检查
function startStatusCheck() {
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status`);
            const status = await response.json();

            if (status.running) {
                updateStatus('running', `${status.current_task} 爬取中...`);
                elements.startBtn.disabled = true;
                elements.stopBtn.disabled = false;

                // 重新加载数据
                loadData();
            } else {
                if (elements.statusIndicator.className === 'status-running') {
                    updateStatus('idle', '就绪');
                    elements.startBtn.disabled = false;
                    elements.stopBtn.disabled = true;
                    loadData();
                }
            }
        } catch (error) {
            console.error('状态检查失败:', error);
        }
    }, 2000);
}

// 更新状态显示
function updateStatus(status, text) {
    elements.statusIndicator.className = `status-${status}`;
    elements.statusText.textContent = text;
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + 'w';
    }
    return num.toString();
}
