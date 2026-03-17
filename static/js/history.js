let historyData = [];
let filteredData = [];
let selectedIds = [];
let currentPage = 1;
let pageSize = 10;
let deleteTargetIds = [];
let isLoading = false;

function init() {
    // 设置默认日期筛选为近30天
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    document.getElementById('filterDateEnd').value = endDate.toISOString().split('T')[0];
    document.getElementById('filterDateStart').value = startDate.toISOString().split('T')[0];
    
    loadHistoryData();
    bindEvents();
}

async function loadHistoryData() {
    if (isLoading) return;
    isLoading = true;
    
    try {
        showLoading();
        
        const response = await fetch('/api/history?limit=1000');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result && result.records) {
            historyData = result.records.map(record => ({
                id: record.id,
                time: record.created_at,
                filename: record.filename,
                rating: record.customer_grade || 'C',
                intention: mapIntentionLevel(record.intention_level),
                stage: record.purchase_stage || '未知',
                tags: record.tags || []
            }));
        } else {
            historyData = [];
        }
        
        filteredData = [...historyData];
        renderTable();
        updatePagination();
        
    } catch (error) {
        console.error('加载历史记录失败:', error);
        showError('加载历史记录失败: ' + error.message);
        historyData = [];
        filteredData = [];
        renderTable();
        updatePagination();
    } finally {
        isLoading = false;
        hideLoading();
    }
}

function mapIntentionLevel(level) {
    const map = {
        '高': 'high',
        '中': 'medium',
        '低': 'low',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
        '': 'low'
    };
    return map[level] || 'low';
}

function bindEvents() {
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    document.getElementById('resetBtn').addEventListener('click', handleReset);
    document.getElementById('selectAll').addEventListener('change', handleSelectAll);
    document.getElementById('compareBtn').addEventListener('click', handleCompare);
    document.getElementById('batchDeleteBtn').addEventListener('click', handleBatchDelete);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

    document.getElementById('searchKeyword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
}

function showLoading() {
    const tbody = document.getElementById('historyTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: var(--text-secondary);">加载中...</td></tr>';
    }
}

function hideLoading() {
}

function handleSearch() {
    const keyword = document.getElementById('searchKeyword').value.trim().toLowerCase();
    const rating = document.getElementById('filterRating').value;
    const intention = document.getElementById('filterIntention').value;
    const dateStart = document.getElementById('filterDateStart').value;
    const dateEnd = document.getElementById('filterDateEnd').value;

    filteredData = historyData.filter(item => {
        let match = true;

        if (keyword) {
            const matchFilename = item.filename.toLowerCase().includes(keyword);
            const matchTags = item.tags.some(tag => tag.toLowerCase().includes(keyword));
            match = match && (matchFilename || matchTags);
        }

        if (rating) {
            // 支持匹配 "B" 或 "B类" 格式
            match = match && (item.rating === rating || item.rating === rating + '类');
        }

        if (intention) {
            match = match && item.intention === intention;
        }

        if (dateStart) {
            const itemDate = item.time.split(' ')[0];
            match = match && itemDate >= dateStart;
        }

        if (dateEnd) {
            const itemDate = item.time.split(' ')[0];
            match = match && itemDate <= dateEnd;
        }

        return match;
    });

    currentPage = 1;
    selectedIds = [];
    updateSelectedCount();
    renderTable();
    updatePagination();
}

function handleReset() {
    document.getElementById('searchKeyword').value = '';
    document.getElementById('filterRating').value = '';
    document.getElementById('filterIntention').value = '';
    document.getElementById('filterDateStart').value = '';
    document.getElementById('filterDateEnd').value = '';

    filteredData = [...historyData];
    currentPage = 1;
    selectedIds = [];
    updateSelectedCount();
    renderTable();
    updatePagination();
}

function renderTable() {
    const tbody = document.getElementById('historyTableBody');
    const emptyState = document.getElementById('emptyState');
    const table = document.querySelector('.data-table');
    const pagination = document.getElementById('pagination');

    if (filteredData.length === 0) {
        table.style.display = 'none';
        pagination.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    table.style.display = 'table';
    pagination.style.display = 'flex';
    emptyState.style.display = 'none';

    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, filteredData.length);
    const pageData = filteredData.slice(startIndex, endIndex);

    tbody.innerHTML = pageData.map(item => `
        <tr class="${selectedIds.includes(item.id) ? 'selected' : ''}" data-id="${item.id}">
            <td class="checkbox-cell">
                <input type="checkbox" 
                       ${selectedIds.includes(item.id) ? 'checked' : ''} 
                       onchange="handleSelectItem(${item.id}, this.checked)">
            </td>
            <td class="time-cell">${item.time}</td>
            <td class="filename-cell" title="${item.filename}">${item.filename}</td>
            <td>
                <span class="rating-badge grade-${item.rating.toLowerCase().replace('类', '')}">
                    ${item.rating.replace('类', '')}级骑手
                </span>
            </td>
            <td>
                <span class="intention-badge ${item.intention}">
                    ${getIntentionText(item.intention)}
                </span>
            </td>
            <td>
                <span class="stage-badge">${item.stage}</span>
            </td>
            <td class="tags-cell">
                ${item.tags.map(tag => `<span class="tag-item">${tag}</span>`).join('')}
            </td>
            <td>
                <div class="action-btns">
                    <button class="action-btn view" onclick="viewDetail(${item.id})">查看</button>
                    <button class="action-btn delete" onclick="handleDelete(${item.id})">删除</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function getIntentionText(intention) {
    const map = {
        'high': '高意向',
        'medium': '中意向',
        'low': '低意向'
    };
    return map[intention] || intention;
}

function updatePagination() {
    const total = filteredData.length;
    const totalPages = Math.ceil(total / pageSize);
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationBtns = document.getElementById('paginationBtns');

    paginationInfo.textContent = `共 ${total} 条记录，第 ${currentPage}/${totalPages || 1} 页`;

    if (totalPages <= 1) {
        paginationBtns.innerHTML = '';
        return;
    }

    let btns = [];

    btns.push(`<button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`);

    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        btns.push(`<button class="page-btn" onclick="goToPage(1)">1</button>`);
        if (startPage > 2) {
            btns.push(`<span style="color: var(--text-secondary);">...</span>`);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        btns.push(`<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            btns.push(`<span style="color: var(--text-secondary);">...</span>`);
        }
        btns.push(`<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`);
    }

    btns.push(`<button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`);

    paginationBtns.innerHTML = btns.join('');
}

function goToPage(page) {
    const totalPages = Math.ceil(filteredData.length / pageSize);
    if (page < 1 || page > totalPages) return;

    currentPage = page;
    renderTable();
    updatePagination();

    document.querySelector('.table-wrapper').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleSelectAll(e) {
    const checked = e.target.checked;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, filteredData.length);
    const pageData = filteredData.slice(startIndex, endIndex);

    if (checked) {
        pageData.forEach(item => {
            if (!selectedIds.includes(item.id)) {
                selectedIds.push(item.id);
            }
        });
    } else {
        pageData.forEach(item => {
            const index = selectedIds.indexOf(item.id);
            if (index > -1) {
                selectedIds.splice(index, 1);
            }
        });
    }

    renderTable();
    updateSelectedCount();
}

function handleSelectItem(id, checked) {
    if (checked) {
        if (!selectedIds.includes(id)) {
            selectedIds.push(id);
        }
    } else {
        const index = selectedIds.indexOf(id);
        if (index > -1) {
            selectedIds.splice(index, 1);
        }
    }

    updateSelectAllState();
    renderTable();
    updateSelectedCount();
}

function updateSelectAllState() {
    const selectAll = document.getElementById('selectAll');
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, filteredData.length);
    const pageData = filteredData.slice(startIndex, endIndex);

    const allSelected = pageData.length > 0 && pageData.every(item => selectedIds.includes(item.id));
    selectAll.checked = allSelected;
}

function updateSelectedCount() {
    const countEl = document.getElementById('selectedCount');
    const compareBtn = document.getElementById('compareBtn');
    const batchDeleteBtn = document.getElementById('batchDeleteBtn');

    if (selectedIds.length > 0) {
        countEl.textContent = `已选 ${selectedIds.length} 条`;
        countEl.style.display = 'inline';
    } else {
        countEl.style.display = 'none';
    }

    compareBtn.disabled = selectedIds.length < 2;
    batchDeleteBtn.disabled = selectedIds.length === 0;
}

function viewDetail(id) {
    window.location.href = `/?record_id=${id}`;
}

function handleDelete(id) {
    deleteTargetIds = [id];
    const item = historyData.find(i => i.id === id);
    document.getElementById('deleteModalBody').textContent = 
        `确定要删除记录"${item ? item.filename : id}"吗？此操作不可恢复。`;
    document.getElementById('deleteModal').classList.add('show');
}

function handleBatchDelete() {
    if (selectedIds.length === 0) return;

    deleteTargetIds = [...selectedIds];
    document.getElementById('deleteModalBody').textContent = 
        `确定要删除选中的 ${selectedIds.length} 条记录吗？此操作不可恢复。`;
    document.getElementById('deleteModal').classList.add('show');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('show');
    deleteTargetIds = [];
}

async function confirmDelete() {
    if (deleteTargetIds.length === 0) {
        closeDeleteModal();
        return;
    }
    
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = '删除中...';
    confirmBtn.disabled = true;
    
    try {
        const deletePromises = deleteTargetIds.map(id => 
            fetch(`/api/history/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
        );
        
        const results = await Promise.all(deletePromises);
        
        const failedDeletes = [];
        for (let i = 0; i < results.length; i++) {
            const response = results[i];
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                failedDeletes.push({
                    id: deleteTargetIds[i],
                    status: response.status,
                    error: errorData.error || '未知错误'
                });
            }
        }
        
        if (failedDeletes.length > 0) {
            const failedIds = failedDeletes.map(f => f.id).join(', ');
            showError(`部分记录删除失败 (ID: ${failedIds})，请重试`);
            console.error('删除失败的记录:', failedDeletes);
        } else {
            showSuccess(`成功删除 ${deleteTargetIds.length} 条记录`);
        }
        
        closeDeleteModal();
        
        selectedIds = selectedIds.filter(id => !deleteTargetIds.includes(id));
        
        await loadHistoryData();
        
        handleSearch();
        
    } catch (error) {
        console.error('删除操作出错:', error);
        showError('删除操作失败: ' + error.message);
        closeDeleteModal();
    } finally {
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        deleteTargetIds = [];
    }
}

function handleCompare() {
    if (selectedIds.length < 2) {
        showError('请至少选择2条记录进行对比');
        return;
    }

    const compareGrid = document.getElementById('compareGrid');
    const selectedItems = historyData.filter(item => selectedIds.includes(item.id));

    compareGrid.innerHTML = selectedItems.map(item => `
        <div class="compare-card">
            <div class="compare-card-header">
                <span class="compare-card-title">${item.filename}</span>
                <span class="compare-card-time">${item.time}</span>
            </div>
            <div class="compare-item">
                <span class="compare-item-label">骑手等级</span>
                <span class="compare-item-value">
                    <span class="rating-badge grade-${item.rating.toLowerCase()}">${item.rating}级</span>
                </span>
            </div>
            <div class="compare-item">
                <span class="compare-item-label">意向强度</span>
                <span class="compare-item-value">
                    <span class="intention-badge ${item.intention}">${getIntentionText(item.intention)}</span>
                </span>
            </div>
            <div class="compare-item">
                <span class="compare-item-label">从业阶段</span>
                <span class="compare-item-value">${item.stage}</span>
            </div>
            <div class="compare-item">
                <span class="compare-item-label">标签</span>
                <span class="compare-item-value">${item.tags.join('、')}</span>
            </div>
        </div>
    `).join('');

    document.getElementById('compareModal').classList.add('show');
}

function closeCompareModal() {
    document.getElementById('compareModal').classList.remove('show');
}

function showError(message) {
    const errorEl = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorEl.style.display = 'flex';

    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <span class="error-icon">✓</span>
        <span>${message}</span>
    `;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => successDiv.remove(), 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', init);
