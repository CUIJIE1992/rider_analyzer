// 全局变量
let selectedFile = null;
let analysisResults = null;
let currentMode = 'file'; // 'file' 或 'text'

// 批量上传相关变量
let batchFiles = [];
let batchResults = [];
let isBatchProcessing = false;
let currentBatchIndex = 0;

// DOM元素
let uploadArea, fileInput, selectBtn, filePreview, fileName, fileSize, removeBtn;
let progressSection, progressFill, progressText, progressPercent;
let resultsSection, errorMessage, errorText;
let textSection, transcriptInput, charCount, analyzeTextBtn;

// 批量上传DOM元素
let batchQueueSection, batchFileList, batchProgressSection, batchProgressFill;
let batchProgressText, batchProgressPercent, batchCurrentFile, batchSummarySection;
let batchSummaryList, batchExportBtn, batchClearBtn;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化DOM元素引用
    uploadArea = document.getElementById('uploadArea');
    fileInput = document.getElementById('fileInput');
    selectBtn = document.getElementById('selectBtn');
    filePreview = document.getElementById('filePreview');
    fileName = document.getElementById('fileName');
    fileSize = document.getElementById('fileSize');
    removeBtn = document.getElementById('removeBtn');
    progressSection = document.getElementById('progressSection');
    progressFill = document.getElementById('progressFill');
    progressText = document.getElementById('progressText');
    progressPercent = document.getElementById('progressPercent');
    resultsSection = document.getElementById('resultsSection');
    errorMessage = document.getElementById('errorMessage');
    errorText = document.getElementById('errorText');
    textSection = document.getElementById('textSection');
    transcriptInput = document.getElementById('transcriptInput');
    charCount = document.getElementById('charCount');
    analyzeTextBtn = document.getElementById('analyzeTextBtn');
    
    // 初始化批量上传DOM元素
    batchQueueSection = document.getElementById('batchQueueSection');
    batchFileList = document.getElementById('batchFileList');
    batchProgressSection = document.getElementById('batchProgressSection');
    batchProgressFill = document.getElementById('batchProgressFill');
    batchProgressText = document.getElementById('batchProgressText');
    batchProgressPercent = document.getElementById('batchProgressPercent');
    batchCurrentFile = document.getElementById('batchCurrentFile');
    batchSummarySection = document.getElementById('batchSummarySection');
    batchSummaryList = document.getElementById('batchSummaryList');
    batchExportBtn = document.getElementById('batchExportBtn');
    batchClearBtn = document.getElementById('batchClearBtn');
    
    // 初始化功能
    initUpload();
    initTabs();
    initModeSwitch();
    initTextInput();
    initBatchUpload();
    
    // 检查URL参数，如果有record_id则加载历史记录
    checkAndLoadRecordFromUrl();
});

// 初始化模式切换
function initModeSwitch() {
    const modeTabs = document.querySelectorAll('.mode-tab');
    
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.getAttribute('data-mode');
            
            // 更新标签状态
            modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 切换显示区域
            if (mode === 'file') {
                document.getElementById('uploadSection').style.display = 'block';
                document.getElementById('textSection').style.display = 'none';
                currentMode = 'file';
            } else {
                document.getElementById('uploadSection').style.display = 'none';
                document.getElementById('textSection').style.display = 'block';
                currentMode = 'text';
            }
        });
    });
}

// 初始化文本输入
function initTextInput() {
    if (transcriptInput) {
        transcriptInput.addEventListener('input', () => {
            const text = transcriptInput.value;
            if (charCount) {
                charCount.textContent = text.length + ' 字符';
            }
        });
    }
    
    if (analyzeTextBtn) {
        analyzeTextBtn.addEventListener('click', () => {
            analyzeTranscript();
        });
    }
}

// 分析转录文本
async function analyzeTranscript() {
    const transcript = transcriptInput ? transcriptInput.value.trim() : '';
    
    if (!transcript) {
        showError('请输入转录文本');
        return;
    }
    
    try {
        if (progressSection) {
            progressSection.style.display = 'block';
            progressSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        showProgress('解析文本...', 30);
        updateStep(1, 'completed');
        updateStep(2, 'completed');
        updateStep(3, 'active');
        
        const response = await fetch('/api/analyze-transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ transcript: transcript })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showProgress('AI分析完成', 100);
            updateStep(4, 'completed');
            analysisResults = result;
            
            setTimeout(() => {
                displayResults(result);
            }, 500);
        } else {
            showError(result.error || '分析失败');
            hideProgress();
        }
    } catch (error) {
        showError('分析失败: ' + error.message);
        hideProgress();
    }
}

// 初始化上传功能
function initUpload() {
    // 点击选择文件按钮
    if (selectBtn) {
        selectBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            if (fileInput) {
                fileInput.click();
            }
        });
    }
    
    // 点击上传区域
    if (uploadArea) {
        uploadArea.addEventListener('click', function(e) {
            if (e.target !== selectBtn && !e.target.closest('.btn')) {
                if (fileInput) {
                    fileInput.click();
                }
            }
        });
    }

    // 文件选择变化 - 支持多文件
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            handleFileSelect(e);
        });
    }

    // 拖放功能 - 支持多文件
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        });
    }

    // 移除文件
    if (removeBtn) {
        removeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            removeFile();
        });
    }
}

// 处理文件选择
function handleFileSelect(e) {
    const files = e.target.files;
    if (files && files.length > 0) {
        handleFiles(files);
    }
}

// 处理多个文件
function handleFiles(files) {
    const validFiles = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        if (!file.name.toLowerCase().endsWith('.mp3')) {
            showError(`文件 "${file.name}" 不是MP3格式，已跳过`);
            continue;
        }
        
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            showError(`文件 "${file.name}" 超过50MB，已跳过`);
            continue;
        }
        
        const exists = batchFiles.some(f => f.name === file.name && f.size === file.size);
        if (exists) {
            showError(`文件 "${file.name}" 已在队列中，已跳过`);
            continue;
        }
        
        validFiles.push({
            file: file,
            name: file.name,
            size: file.size,
            status: 'pending',
            result: null,
            error: null
        });
    }
    
    if (validFiles.length > 0) {
        batchFiles = batchFiles.concat(validFiles);
        renderBatchFileList();
        
        if (batchQueueSection) {
            batchQueueSection.style.display = 'block';
        }
        
        showSuccess(`已添加 ${validFiles.length} 个文件到队列`);
    }
}

// 处理文件
function handleFile(file) {
    // 验证文件类型
    if (!file.name.toLowerCase().endsWith('.mp3')) {
        showError('请选择MP3格式的文件');
        return;
    }

    // 验证文件大小（50MB）
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('文件大小不能超过50MB');
        return;
    }

    selectedFile = file;
    
    // 显示文件预览
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (filePreview) filePreview.style.display = 'block';
    
    // 自动上传
    uploadFile();
}

// 移除文件
function removeFile() {
    selectedFile = null;
    if (fileInput) fileInput.value = '';
    if (filePreview) filePreview.style.display = 'none';
    if (progressSection) progressSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';
}

// 上传文件
async function uploadFile() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        showProgress('上传文件中...', 10);
        updateStep(1, 'active');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showProgress('文件上传成功', 30);
            updateStep(1, 'completed');
            processAudio(result.filename);
        } else {
            showError(result.error || '上传失败');
            hideProgress();
        }
    } catch (error) {
        showError('上传失败: ' + error.message);
        hideProgress();
    }
}

// 处理音频
async function processAudio(filename) {
    try {
        showProgress('分离语音...', 50);
        updateStep(2, 'active');
        
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: filename })
        });

        const result = await response.json();

        if (result.success) {
            showProgress('处理完成', 100);
            updateStep(4, 'completed');
            analysisResults = result;
            
            setTimeout(() => {
                displayResults(result);
            }, 500);
        } else {
            showError(result.error || '处理失败');
            hideProgress();
        }
    } catch (error) {
        showError('处理失败: ' + error.message);
        hideProgress();
    }
}

// 显示进度
function showProgress(text, percent) {
    if (progressSection) progressSection.style.display = 'block';
    if (progressText) progressText.textContent = text;
    if (progressFill) progressFill.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';
}

// 隐藏进度
function hideProgress() {
    setTimeout(() => {
        if (progressSection) progressSection.style.display = 'none';
    }, 1000);
}

// 更新步骤状态
function updateStep(stepNum, status) {
    const step = document.getElementById('step' + stepNum);
    if (step) {
        step.classList.remove('active', 'completed');
        if (status) {
            step.classList.add(status);
        }
    }
}

// 显示结果
function displayResults(data) {
    hideProgress();
    if (resultsSection) resultsSection.style.display = 'block';
    
    const analysis = data.analysis || {};
    
    let role1 = '说话人 1';
    let role2 = '说话人 2';
    
    if (analysis['角色识别']) {
        role1 = analysis['角色识别']['说话人1'] || '说话人 1';
        role2 = analysis['角色识别']['说话人2'] || '说话人 2';
    }
    
    const sentiment1Label = document.getElementById('sentiment1Label');
    const sentiment2Label = document.getElementById('sentiment2Label');
    const viewpoints1Label = document.getElementById('viewpoints1Label');
    const viewpoints2Label = document.getElementById('viewpoints2Label');
    
    if (sentiment1Label) sentiment1Label.textContent = role1;
    if (sentiment2Label) sentiment2Label.textContent = role2;
    if (viewpoints1Label) viewpoints1Label.textContent = role1;
    if (viewpoints2Label) viewpoints2Label.textContent = role2;
    
    displayChatMessages(data.speaker1, data.speaker2, role1, role2);
    
    displayAnalysis(data.analysis);
    
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// 显示微信风格对话
function displayChatMessages(speaker1Data, speaker2Data, role1, role2) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    let messages = [];
    
    if (Array.isArray(speaker1Data)) {
        speaker1Data.forEach((item, index) => {
            messages.push({
                speaker: 1,
                text: typeof item === 'object' ? item.text : item,
                order: index * 2
            });
        });
    }
    
    if (Array.isArray(speaker2Data)) {
        speaker2Data.forEach((item, index) => {
            messages.push({
                speaker: 2,
                text: typeof item === 'object' ? item.text : item,
                order: index * 2 + 1
            });
        });
    }
    
    messages.sort((a, b) => a.order - b.order);
    
    let html = '';
    messages.forEach((msg, index) => {
        const speakerClass = msg.speaker === 1 ? 'speaker1' : 'speaker2';
        const roleName = msg.speaker === 1 ? role1 : role2;
        const avatar = msg.speaker === 1 ? '👨‍💼' : '👤';
        
        html += `
            <div class="chat-message ${speakerClass}">
                <div class="chat-avatar">${avatar}</div>
                <div class="chat-bubble-wrapper">
                    <div class="chat-role-name">${roleName}</div>
                    <div class="chat-bubble">${highlightKeywords(msg.text)}</div>
                </div>
            </div>
        `;
    });
    
    chatMessages.innerHTML = html;
}

// 复制聊天文本
function copyChatText() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const bubbles = chatMessages.querySelectorAll('.chat-bubble');
    const roleNames = chatMessages.querySelectorAll('.chat-role-name');
    
    let text = '';
    bubbles.forEach((bubble, index) => {
        const role = roleNames[index] ? roleNames[index].textContent : '';
        text += `${role}：${bubble.textContent}\n`;
    });
    
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('对话文本已复制到剪贴板');
    }).catch(err => {
        showError('复制失败: ' + err.message);
    });
}

function highlightKeywords(text) {
    if (!text) return text;
    
    let result = text;
    
    const pricePatterns = [
        /(\d+(?:\.\d+)?\s*[万百千万亿]+(?:\/平(?:米)?)?)/g,
        /(\d+(?:\.\d+)?\s*元(?:\/平(?:米)?)?)/g,
        /(\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:万|元)?(?:\/平(?:米)?)?)/g,
        /(单价\s*[:：]?\s*\d+(?:\.\d+)?(?:万|元)?(?:\/平(?:米)?)?)/g,
        /(总价\s*[:：]?\s*\d+(?:\.\d+)?(?:万|元)?)/g
    ];
    
    const areaPatterns = [
        /(\d+(?:\.\d+)?\s*(?:平(?:米)?|平方米|m²))/g,
        /(三室两厅|两室一厅|一室一厅|四室两厅|三室一厅|两室两厅|一居室|两居室|三居室|四居室)/g,
        /(\d+室\d+厅)/g
    ];
    
    const timePatterns = [
        /(明天|后天|大后天)/g,
        /(今天|今晚)/g,
        /(周[一二三四五六日]|周末)/g,
        /(下[周月]|上[周月])/g,
        /(上午|下午|中午|晚上|傍晚|凌晨)/g,
        /(\d{1,2}[点时](?:\d{1,2}分?)?)/g,
        /(这[个]?[周月]|这[个]?周末)/g,
        /([下上]午\s*\d{1,2}[点时](?:\d{1,2}分?)?)/g
    ];
    
    const phonePatterns = [
        /(1[3-9]\d{9})/g,
        /(1[3-9]\d-\d{4}-\d{4})/g,
        /(1[3-9]\d\s*\d{4}\s*\d{4})/g,
        /(1[3-9][\dXx]{2}[\s-]?[\dXx]{4}[\s-]?[\dXx]{4})/g
    ];
    
    const placeholders = [];
    
    function savePlaceholder(type, match) {
        const index = placeholders.length;
        placeholders.push({ type, match });
        return `__PLACEHOLDER_${index}__`;
    }
    
    phonePatterns.forEach(pattern => {
        result = result.replace(pattern, (match) => {
            return savePlaceholder('phone', match);
        });
    });
    
    pricePatterns.forEach(pattern => {
        result = result.replace(pattern, (match) => {
            return savePlaceholder('price', match);
        });
    });
    
    areaPatterns.forEach(pattern => {
        result = result.replace(pattern, (match) => {
            return savePlaceholder('area', match);
        });
    });
    
    timePatterns.forEach(pattern => {
        result = result.replace(pattern, (match) => {
            return savePlaceholder('time', match);
        });
    });
    
    result = result
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    placeholders.forEach((item, index) => {
        const escapedMatch = item.match
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        let className = '';
        switch (item.type) {
            case 'price':
                className = 'highlight-price';
                break;
            case 'area':
                className = 'highlight-area';
                break;
            case 'time':
                className = 'highlight-time';
                break;
            case 'phone':
                className = 'highlight-phone';
                break;
        }
        
        result = result.replace(`__PLACEHOLDER_${index}__`, `<span class="${className}">${escapedMatch}</span>`);
    });
    
    return result;
}

function displayTranscript(elementId, textData) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (Array.isArray(textData)) {
        let html = '';
        textData.forEach(item => {
            if (typeof item === 'object') {
                html += `<div class="transcript-item">
                    <span class="timestamp">[${item.timestamp || ''}]</span>
                    <span class="text">${highlightKeywords(item.text || '')}</span>
                </div>`;
            } else {
                html += `<div class="transcript-item">${highlightKeywords(item)}</div>`;
            }
        });
        element.innerHTML = html;
    } else {
        element.innerHTML = `<div class="transcript-item">${highlightKeywords(textData || '无内容')}</div>`;
    }
}

// 显示AI分析
function displayAnalysis(analysis) {
    if (!analysis) return;
    
    // 通话概要
    displayOverview(analysis['通话概要']);
    
    // 客户评级
    displayRating(analysis['客户评级']);
    
    // 购房意向
    displayIntention(analysis['购房意向']);
    
    // 购房阶段
    displayStage(analysis['购房阶段']);
    
    // 核心关注点
    displayConcerns(analysis['核心关注点']);
    
    // 竞品分析
    displayCompetitor(analysis['竞品分析']);
    
    // 情感分析
    displaySentiment(analysis['情感分析']);
    
    // 关键信息
    displayKeyInfo(analysis['关键信息']);
    
    // 总结
    const summaryText = document.getElementById('summaryText');
    if (summaryText) summaryText.textContent = analysis['总结'] || '暂无总结';
}

// 显示通话概要
function displayOverview(overview) {
    const container = document.getElementById('overviewStats');
    if (!container || !overview) return;
    
    container.innerHTML = `
        <div class="overview-stat-item">
            <div class="overview-stat-value">${overview['通话时长估算'] || '-'}</div>
            <div class="overview-stat-label">通话时长</div>
        </div>
        <div class="overview-stat-item">
            <div class="overview-stat-value">${overview['有效沟通程度'] || '-'}</div>
            <div class="overview-stat-label">有效沟通程度</div>
        </div>
        <div class="overview-stat-item">
            <div class="overview-stat-value">${overview['客户响应积极性'] || '-'}</div>
            <div class="overview-stat-label">客户响应积极性</div>
        </div>
    `;
}

function generateCustomerTags(analysis) {
    const tags = [];
    
    if (!analysis) return tags;
    
    const rating = analysis['客户评级'] || {};
    const stage = analysis['购房阶段'] || {};
    const concerns = analysis['核心关注点'] || {};
    
    const intention = rating['购房意向强度'] || '';
    if (intention === '高') {
        tags.push({ text: '高意向客户', class: 'tag-high' });
    } else if (intention === '中') {
        tags.push({ text: '中意向客户', class: 'tag-medium' });
    } else if (intention === '低') {
        tags.push({ text: '低意向客户', class: 'tag-low' });
    }
    
    const grade = rating['综合等级'] || '';
    if (grade === 'A类') {
        tags.push({ text: 'A类优质客户', class: 'tag-premium' });
    }
    
    const allConcerns = [];
    const firstConcern = concerns['第一关注'] || {};
    const secondConcern = concerns['第二关注'] || {};
    const thirdConcern = concerns['第三关注'] || {};
    const otherConcerns = concerns['其他关注'] || [];
    
    if (firstConcern['因素']) allConcerns.push(firstConcern['因素']);
    if (secondConcern['因素']) allConcerns.push(secondConcern['因素']);
    if (thirdConcern['因素']) allConcerns.push(thirdConcern['因素']);
    allConcerns.push(...otherConcerns);
    
    const allConcernsText = allConcerns.join(' ');
    if (allConcernsText.includes('学区') || allConcernsText.includes('教育')) {
        tags.push({ text: '学区关注', class: 'tag-education' });
    }
    if (allConcernsText.includes('交通')) {
        tags.push({ text: '交通关注', class: 'tag-transport' });
    }
    
    const currentStage = stage['当前阶段'] || '';
    if (currentStage.includes('改善')) {
        tags.push({ text: '改善型需求', class: 'tag-improve' });
    } else if (currentStage.includes('刚需') || currentStage.includes('首次')) {
        tags.push({ text: '刚需客户', class: 'tag-first-time' });
    } else if (currentStage.includes('决策')) {
        tags.push({ text: '决策期客户', class: 'tag-decision' });
    }
    
    return tags;
}

function displayRating(rating) {
    const container = document.getElementById('ratingContent');
    if (!container || !rating) return;
    
    const intentionClass = rating['购房意向强度'] === '高' ? 'high' : (rating['购房意向强度'] === '中' ? 'medium' : 'low');
    const purchaseClass = rating['购买力评估'] === '高' ? 'high' : (rating['购买力评估'] === '中' ? 'medium' : 'low');
    const gradeClass = rating['综合等级'] === 'A类' ? 'grade-a' : (rating['综合等级'] === 'B类' ? 'grade-b' : 'grade-c');
    
    const tags = generateCustomerTags(analysisResults ? analysisResults.analysis : null);
    let tagsHtml = '';
    if (tags.length > 0) {
        tagsHtml = `
            <div class="customer-tags">
                <div class="tags-title">🏷️ 客户标签</div>
                <div class="tags-container">
                    ${tags.map(tag => `<span class="customer-tag ${tag.class}">${tag.text}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    // 构建评级维度数据
    const ratingDimensions = [
        { icon: '🎯', label: '意向强度', value: rating['购房意向强度'] || '-', class: intentionClass },
        { icon: '💰', label: '购买力', value: rating['购买力评估'] || '-', class: purchaseClass },
        { icon: '⏱️', label: '决策周期', value: rating['决策周期'] || '-', class: '' },
        { icon: '🏆', label: '综合评级', value: rating['综合等级'] || '-', class: gradeClass }
    ];
    
    container.innerHTML = `
        ${tagsHtml}
        <div class="rating-badges">
            ${ratingDimensions.map(dim => `
                <div class="rating-badge ${dim.class}">
                    <span class="badge-icon">${dim.icon}</span>
                    <span class="badge-label">${dim.label}</span>
                    <span class="badge-value">${dim.value}</span>
                </div>
            `).join('')}
        </div>
        <div class="rating-description">
            <strong>📋 评级说明</strong>
            <p>${rating['等级说明'] || '根据客户购房意向、购买力、决策周期等多维度综合评估，该客户暂无详细评级说明。'}</p>
        </div>
    `;
}

// 显示购房意向
function displayIntention(intention) {
    const container = document.getElementById('intentionGrid');
    if (!container || !intention) return;
    
    const items = [
        { label: '面积需求', value: intention['面积需求'] },
        { label: '价格区间', value: intention['价格区间'] },
        { label: '区域偏好', value: intention['区域偏好'] },
        { label: '户型需求', value: intention['户型需求'] }
    ];
    
    container.innerHTML = items.map(item => `
        <div class="intention-item">
            <div class="intention-label">${item.label}</div>
            <div class="intention-value">${item.value || '未提及'}</div>
        </div>
    `).join('');
}

// 显示购房阶段
function displayStage(stage) {
    const container = document.getElementById('stageContent');
    if (!container || !stage) return;
    
    const stages = ['初步咨询', '需求明确', '决策阶段', '犹豫观望'];
    const currentStage = stage['当前阶段'] || '';
    
    let stageHtml = '<div class="stage-indicator">';
    stages.forEach((s, i) => {
        const isActive = currentStage.includes(s.substring(0, 2));
        stageHtml += `
            <div class="stage-step ${isActive ? 'active' : ''}">
                <div class="stage-step-icon">${i + 1}</div>
                <div class="stage-step-label">${s}</div>
            </div>
        `;
    });
    stageHtml += '</div>';
    
    stageHtml += `<div class="stage-description"><strong>阶段特征：</strong>${stage['阶段特征'] || '暂无描述'}</div>`;
    
    container.innerHTML = stageHtml;
}

// 显示核心关注点
function displayConcerns(concerns) {
    const container = document.getElementById('concernsContent');
    if (!container || !concerns) return;
    
    let html = '';
    
    if (concerns['第一关注']) {
        html += `
            <div class="concern-item">
                <div class="concern-rank rank-1">1</div>
                <div class="concern-info">
                    <div class="concern-factor">${concerns['第一关注']['因素'] || '未提及'}</div>
                    <div class="concern-detail">${concerns['第一关注']['具体内容'] || ''}</div>
                </div>
            </div>
        `;
    }
    
    if (concerns['第二关注']) {
        html += `
            <div class="concern-item">
                <div class="concern-rank rank-2">2</div>
                <div class="concern-info">
                    <div class="concern-factor">${concerns['第二关注']['因素'] || '未提及'}</div>
                    <div class="concern-detail">${concerns['第二关注']['具体内容'] || ''}</div>
                </div>
            </div>
        `;
    }
    
    if (concerns['第三关注']) {
        html += `
            <div class="concern-item">
                <div class="concern-rank rank-3">3</div>
                <div class="concern-info">
                    <div class="concern-factor">${concerns['第三关注']['因素'] || '未提及'}</div>
                    <div class="concern-detail">${concerns['第三关注']['具体内容'] || ''}</div>
                </div>
            </div>
        `;
    }
    
    if (concerns['其他关注'] && concerns['其他关注'].length > 0) {
        html += `<div style="margin-top:15px;padding:15px;background:var(--bg-light);border-radius:8px;">
            <strong>其他关注点：</strong>${concerns['其他关注'].join('、')}
        </div>`;
    }
    
    container.innerHTML = html || '<div style="color:var(--text-secondary);">暂无关注点信息</div>';
}

// 显示竞品分析
function displayCompetitor(competitor) {
    const container = document.getElementById('competitorContent');
    if (!container || !competitor) return;
    
    const tendencyClass = competitor['对比倾向']?.includes('本项目') ? 'positive' : 
                          (competitor['对比倾向']?.includes('竞品') ? 'negative' : 'neutral');
    
    let html = '';
    
    if (competitor['提及竞品'] && competitor['提及竞品'].length > 0) {
        html += '<div class="competitor-list">';
        competitor['提及竞品'].forEach(c => {
            html += `<span class="competitor-tag">${c}</span>`;
        });
        html += '</div>';
    }
    
    html += `
        <div class="competitor-tendency">
            <div class="tendency-label">客户对比倾向</div>
            <div class="tendency-value ${tendencyClass}">${competitor['对比倾向'] || '暂无对比'}</div>
        </div>
    `;
    
    html += '<div class="competitor-compare">';
    html += `
        <div class="compare-section advantages">
            <h4>✅ 本项目优势</h4>
            <ul>
                ${(competitor['本项目优势'] || []).map(a => `<li>${a}</li>`).join('')}
            </ul>
        </div>
        <div class="compare-section disadvantages">
            <h4>⚠️ 本项目劣势</h4>
            <ul>
                ${(competitor['本项目劣势'] || []).map(d => `<li>${d}</li>`).join('')}
            </ul>
        </div>
    `;
    html += '</div>';
    
    container.innerHTML = html;
}

// 显示情感分析
function displaySentiment(sentiment) {
    const container = document.getElementById('sentimentContent');
    if (!container || !sentiment) return;
    
    // 定义情感维度和对应的图标
    const sentimentDimensions = [
        { 
            key: '客户态度', 
            icon: '😊',
            desc: '客户整体情绪倾向'
        },
        { 
            key: '置业顾问表现', 
            icon: '👔',
            desc: '专业度与服务评价'
        },
        { 
            key: '沟通效果', 
            icon: '💬',
            desc: '信息传递与理解程度'
        }
    ];
    
    // 获取情感倾向的评分样式
    function getSentimentClass(value) {
        if (!value) return '';
        const val = value.toLowerCase();
        if (val.includes('积极') || val.includes('好') || val.includes('高')) return 'positive';
        if (val.includes('消极') || val.includes('差') || val.includes('低')) return 'negative';
        return 'neutral';
    }
    
    container.innerHTML = sentimentDimensions.map(dim => {
        const value = sentiment[dim.key] || '-';
        const scoreClass = getSentimentClass(value);
        const scoreIcon = scoreClass === 'positive' ? '✓' : scoreClass === 'negative' ? '✗' : '−';
        
        return `
            <div class="sentiment-box">
                <span class="sentiment-box-icon">${dim.icon}</span>
                <div class="sentiment-box-label">${dim.key}</div>
                <div class="sentiment-box-value">${value}</div>
                ${value !== '-' ? `<div class="sentiment-score ${scoreClass}">${scoreIcon} ${scoreClass === 'positive' ? '良好' : scoreClass === 'negative' ? '需改进' : '一般'}</div>` : ''}
            </div>
        `;
    }).join('');
}

// 显示关键信息
function displayKeyInfo(keyInfo) {
    const container = document.getElementById('keyInfoGrid');
    if (!container || !keyInfo) return;
    
    const items = [
        { label: '📞 联系方式', value: keyInfo['联系方式'] },
        { label: '📅 看房安排', value: keyInfo['看房安排'] },
        { label: '📝 特殊需求', value: keyInfo['特殊需求'] }
    ];
    
    container.innerHTML = items.map(item => `
        <div class="key-info-item">
            <div class="key-info-label">${item.label}</div>
            <div class="key-info-value">${item.value || '暂无信息'}</div>
        </div>
    `).join('');
}

// 显示跟进建议
function displayFollowup(followup) {
    const container = document.getElementById('followupContent');
    if (!container || !followup) return;
    
    let html = '';
    
    if (followup['推荐话术'] && followup['推荐话术'].length > 0) {
        html += `
            <div class="followup-section">
                <h4>💬 推荐话术要点</h4>
                <ul class="followup-list">
                    ${followup['推荐话术'].map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (followup['卖点强调'] && followup['卖点强调'].length > 0) {
        html += `
            <div class="followup-section">
                <h4>⭐ 差异化卖点强调</h4>
                <ul class="followup-list">
                    ${followup['卖点强调'].map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (followup['异议处理'] && followup['异议处理'].length > 0) {
        html += `
            <div class="followup-section">
                <h4>🛡️ 异议处理建议</h4>
                <ul class="followup-list">
                    ${followup['异议处理'].map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (followup['下一步计划']) {
        html += `
            <div class="followup-section">
                <h4>📋 下一步跟进计划</h4>
                <div class="followup-plan">${followup['下一步计划']}</div>
            </div>
        `;
    }
    
    container.innerHTML = html || '<div style="color:var(--text-secondary);">暂无跟进建议</div>';
}

// 显示列表
function displayList(elementId, items) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (Array.isArray(items)) {
        element.innerHTML = items.map(item => `<li>${item}</li>`).join('');
    } else if (items) {
        element.innerHTML = `<li>${items}</li>`;
    } else {
        element.innerHTML = '<li>无</li>';
    }
}

// 初始化标签页
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-tab');
            
            // 移除所有活动状态
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // 添加当前活动状态
            tab.classList.add('active');
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add('active');
        });
    });
}

// 复制文本
function copyText(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('文本已复制到剪贴板');
    }).catch(err => {
        showError('复制失败: ' + err.message);
    });
}

// 下载PDF报告
async function downloadPDF() {
    if (!analysisResults) {
        showError('没有可下载的结果');
        return;
    }
    
    showSuccess('正在生成PDF报告，请稍候...');
    
    try {
        const response = await fetch('/api/export-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                analysis: analysisResults.analysis,
                speaker1: analysisResults.speaker1,
                speaker2: analysisResults.speaker2
            })
        });
        
        if (!response.ok) {
            throw new Error('PDF生成失败');
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `购房电话分析报告_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.pdf`;
        a.click();
        
        URL.revokeObjectURL(url);
        showSuccess('PDF报告已下载');
        
    } catch (err) {
        showError('PDF生成失败: ' + err.message);
    }
}

// 下载结果
function downloadResults() {
    if (!analysisResults) {
        showError('没有可下载的结果');
        return;
    }

    const content = generateReport();
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = '通话分析报告.txt';
    a.click();
    
    URL.revokeObjectURL(url);
    showSuccess('报告已下载');
}

// 生成报告
function generateReport() {
    let report = '购房电话分析报告\n';
    report += '=' .repeat(50) + '\n\n';
    
    const analysis = analysisResults.analysis || {};
    const role1 = analysis['角色识别'] ? analysis['角色识别']['说话人1'] : '置业顾问';
    const role2 = analysis['角色识别'] ? analysis['角色识别']['说话人2'] : '客户';
    
    // 对话记录
    report += `【${role1}】\n`;
    if (Array.isArray(analysisResults.speaker1)) {
        analysisResults.speaker1.forEach(item => {
            const text = typeof item === 'object' ? item.text : item;
            report += `${text || ''}\n`;
        });
    }
    
    report += `\n【${role2}】\n`;
    if (Array.isArray(analysisResults.speaker2)) {
        analysisResults.speaker2.forEach(item => {
            const text = typeof item === 'object' ? item.text : item;
            report += `${text || ''}\n`;
        });
    }
    
    report += '\n' + '='.repeat(50) + '\n';
    report += '购房电话分析结果\n';
    report += '='.repeat(50) + '\n\n';
    
    // 通话概要
    if (analysis['通话概要']) {
        report += '【通话概要】\n';
        report += `  通话时长: ${analysis['通话概要']['通话时长估算'] || '-'}\n`;
        report += `  有效沟通程度: ${analysis['通话概要']['有效沟通程度'] || '-'}\n`;
        report += `  客户响应积极性: ${analysis['通话概要']['客户响应积极性'] || '-'}\n\n`;
    }
    
    // 客户评级
    if (analysis['客户评级']) {
        report += '【客户评级】\n';
        report += `  购房意向强度: ${analysis['客户评级']['购房意向强度'] || '-'}\n`;
        report += `  购买力评估: ${analysis['客户评级']['购买力评估'] || '-'}\n`;
        report += `  决策周期: ${analysis['客户评级']['决策周期'] || '-'}\n`;
        report += `  综合等级: ${analysis['客户评级']['综合等级'] || '-'}\n`;
        report += `  等级说明: ${analysis['客户评级']['等级说明'] || '-'}\n\n`;
    }
    
    // 购房意向
    if (analysis['购房意向']) {
        report += '【购房意向】\n';
        report += `  面积需求: ${analysis['购房意向']['面积需求'] || '未提及'}\n`;
        report += `  价格区间: ${analysis['购房意向']['价格区间'] || '未提及'}\n`;
        report += `  区域偏好: ${analysis['购房意向']['区域偏好'] || '未提及'}\n`;
        report += `  户型需求: ${analysis['购房意向']['户型需求'] || '未提及'}\n\n`;
    }
    
    // 购房阶段
    if (analysis['购房阶段']) {
        report += '【购房阶段】\n';
        report += `  当前阶段: ${analysis['购房阶段']['当前阶段'] || '-'}\n`;
        report += `  阶段特征: ${analysis['购房阶段']['阶段特征'] || '-'}\n\n`;
    }
    
    // 核心关注点
    if (analysis['核心关注点']) {
        report += '【客户核心关注点】\n';
        if (analysis['核心关注点']['第一关注']) {
            report += `  1. ${analysis['核心关注点']['第一关注']['因素']}: ${analysis['核心关注点']['第一关注']['具体内容']}\n`;
        }
        if (analysis['核心关注点']['第二关注']) {
            report += `  2. ${analysis['核心关注点']['第二关注']['因素']}: ${analysis['核心关注点']['第二关注']['具体内容']}\n`;
        }
        if (analysis['核心关注点']['第三关注']) {
            report += `  3. ${analysis['核心关注点']['第三关注']['因素']}: ${analysis['核心关注点']['第三关注']['具体内容']}\n`;
        }
        if (analysis['核心关注点']['其他关注'] && analysis['核心关注点']['其他关注'].length > 0) {
            report += `  其他: ${analysis['核心关注点']['其他关注'].join('、')}\n`;
        }
        report += '\n';
    }
    
    // 竞品分析
    if (analysis['竞品分析']) {
        report += '【竞品对比分析】\n';
        if (analysis['竞品分析']['提及竞品'] && analysis['竞品分析']['提及竞品'].length > 0) {
            report += `  提及竞品: ${analysis['竞品分析']['提及竞品'].join('、')}\n`;
        }
        report += `  对比倾向: ${analysis['竞品分析']['对比倾向'] || '-'}\n`;
        if (analysis['竞品分析']['本项目优势'] && analysis['竞品分析']['本项目优势'].length > 0) {
            report += `  本项目优势:\n`;
            analysis['竞品分析']['本项目优势'].forEach(a => report += `    ✓ ${a}\n`);
        }
        if (analysis['竞品分析']['本项目劣势'] && analysis['竞品分析']['本项目劣势'].length > 0) {
            report += `  本项目劣势:\n`;
            analysis['竞品分析']['本项目劣势'].forEach(d => report += `    ✗ ${d}\n`);
        }
        report += '\n';
    }
    
    // 情感分析
    if (analysis['情感分析']) {
        report += '【情感与沟通分析】\n';
        report += `  客户态度: ${analysis['情感分析']['客户态度'] || '-'}\n`;
        report += `  置业顾问表现: ${analysis['情感分析']['置业顾问表现'] || '-'}\n`;
        report += `  沟通效果: ${analysis['情感分析']['沟通效果'] || '-'}\n\n`;
    }
    
    // 关键信息
    if (analysis['关键信息']) {
        report += '【关键信息】\n';
        report += `  联系方式: ${analysis['关键信息']['联系方式'] || '暂无'}\n`;
        report += `  看房安排: ${analysis['关键信息']['看房安排'] || '暂无'}\n`;
        report += `  特殊需求: ${analysis['关键信息']['特殊需求'] || '暂无'}\n\n`;
    }
    
    // 跟进建议
    if (analysis['跟进建议']) {
        report += '【跟进策略建议】\n';
        if (analysis['跟进建议']['推荐话术'] && analysis['跟进建议']['推荐话术'].length > 0) {
            report += `  推荐话术要点:\n`;
            analysis['跟进建议']['推荐话术'].forEach(s => report += `    • ${s}\n`);
        }
        if (analysis['跟进建议']['卖点强调'] && analysis['跟进建议']['卖点强调'].length > 0) {
            report += `  差异化卖点强调:\n`;
            analysis['跟进建议']['卖点强调'].forEach(s => report += `    • ${s}\n`);
        }
        if (analysis['跟进建议']['异议处理'] && analysis['跟进建议']['异议处理'].length > 0) {
            report += `  异议处理建议:\n`;
            analysis['跟进建议']['异议处理'].forEach(s => report += `    • ${s}\n`);
        }
        if (analysis['跟进建议']['下一步计划']) {
            report += `  下一步计划: ${analysis['跟进建议']['下一步计划']}\n`;
        }
        report += '\n';
    }
    
    // 总结
    report += '【分析总结】\n';
    report += `${analysis['总结'] || '暂无总结'}\n`;
    
    return report;
}

// 检查URL参数并加载历史记录
function checkAndLoadRecordFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const recordId = urlParams.get('record_id');
    
    if (recordId) {
        loadRecordById(recordId);
    }
}

// 根据ID加载历史记录
async function loadRecordById(id) {
    try {
        const response = await fetch(`/api/history/${id}`);
        if (!response.ok) {
            showError('加载历史记录失败');
            return;
        }
        
        const record = await response.json();
        if (record && record.id) {
            displayHistoryRecord(record);
        } else {
            showError('未找到该记录');
        }
    } catch (error) {
        console.error('加载历史记录出错:', error);
        showError('加载历史记录时发生错误');
    }
}

// 显示历史记录的分析结果
function displayHistoryRecord(record) {
    console.log('[displayHistoryRecord] 开始显示历史记录:', record);
    
    if (!record.analysis_data) {
        console.error('[displayHistoryRecord] 没有分析数据');
        showError('该记录没有分析数据');
        return;
    }
    
    let analysis;
    try {
        analysis = typeof record.analysis_data === 'string' 
            ? JSON.parse(record.analysis_data) 
            : record.analysis_data;
        console.log('[displayHistoryRecord] 解析后的 analysis:', analysis);
    } catch (e) {
        console.error('[displayHistoryRecord] 分析数据解析失败:', e);
        showError('分析数据格式错误');
        return;
    }
    
    if (!analysis || typeof analysis !== 'object') {
        console.error('[displayHistoryRecord] analysis 不是有效对象:', analysis);
        showError('分析数据格式无效');
        return;
    }
    
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    let role1 = '说话人 1';
    let role2 = '说话人 2';
    
    if (analysis['角色识别']) {
        role1 = analysis['角色识别']['说话人1'] || '说话人 1';
        role2 = analysis['角色识别']['说话人2'] || '说话人 2';
    }
    console.log('[displayHistoryRecord] 角色识别 - role1:', role1, 'role2:', role2);
    
    const sentiment1Label = document.getElementById('sentiment1Label');
    const sentiment2Label = document.getElementById('sentiment2Label');
    const viewpoints1Label = document.getElementById('viewpoints1Label');
    const viewpoints2Label = document.getElementById('viewpoints2Label');
    
    if (sentiment1Label) sentiment1Label.textContent = role1;
    if (sentiment2Label) sentiment2Label.textContent = role2;
    if (viewpoints1Label) viewpoints1Label.textContent = role1;
    if (viewpoints2Label) viewpoints2Label.textContent = role2;
    
    let speaker1Data = [];
    let speaker2Data = [];
    
    if (record.speaker1_data) {
        try {
            speaker1Data = typeof record.speaker1_data === 'string' 
                ? JSON.parse(record.speaker1_data) 
                : record.speaker1_data;
            if (!Array.isArray(speaker1Data)) speaker1Data = [];
        } catch (e) {
            console.warn('[displayHistoryRecord] speaker1_data 解析失败:', e);
            speaker1Data = [];
        }
    }
    
    if (record.speaker2_data) {
        try {
            speaker2Data = typeof record.speaker2_data === 'string' 
                ? JSON.parse(record.speaker2_data) 
                : record.speaker2_data;
            if (!Array.isArray(speaker2Data)) speaker2Data = [];
        } catch (e) {
            console.warn('[displayHistoryRecord] speaker2_data 解析失败:', e);
            speaker2Data = [];
        }
    }
    
    console.log('[displayHistoryRecord] speaker1Data 长度:', speaker1Data.length);
    console.log('[displayHistoryRecord] speaker2Data 长度:', speaker2Data.length);
    
    displayChatMessages(speaker1Data, speaker2Data, role1, role2);
    
    analysisResults = {
        analysis: analysis,
        speaker1: speaker1Data,
        speaker2: speaker2Data
    };
    console.log('[displayHistoryRecord] 设置 analysisResults:', analysisResults);
    
    console.log('[displayHistoryRecord] 调用 displayAnalysis');
    displayAnalysis(analysis);
    
    document.title = `分析结果 - ${record.filename || '历史记录'}`;
    
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    console.log('[displayHistoryRecord] 显示完成');
}

// 重置应用
function resetApp() {
    removeFile();
    if (transcriptInput) transcriptInput.value = '';
    if (charCount) charCount.textContent = '0 字符';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 显示错误
function showError(message) {
    if (errorText) errorText.textContent = message;
    if (errorMessage) errorMessage.style.display = 'flex';
    
    setTimeout(() => {
        hideError();
    }, 5000);
}

// 隐藏错误
function hideError() {
    if (errorMessage) errorMessage.style.display = 'none';
}

// 显示成功提示
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `<span class="success-icon">✓</span><span>${message}</span>`;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 初始化批量上传功能
function initBatchUpload() {
    if (batchExportBtn) {
        batchExportBtn.addEventListener('click', function() {
            exportBatchResults();
        });
    }
    
    if (batchClearBtn) {
        batchClearBtn.addEventListener('click', function() {
            clearBatchFiles();
        });
    }
}

// 渲染文件队列列表
function renderBatchFileList() {
    if (!batchFileList) return;
    
    if (batchFiles.length === 0) {
        batchFileList.innerHTML = '<div class="empty-queue">暂无文件，请选择或拖拽文件到上传区域</div>';
        return;
    }
    
    let html = '';
    batchFiles.forEach((item, index) => {
        const statusClass = getStatusClass(item.status);
        const statusText = getStatusText(item.status);
        
        html += `
            <div class="batch-file-item ${statusClass}" data-index="${index}">
                <div class="batch-file-info">
                    <div class="batch-file-icon">🎵</div>
                    <div class="batch-file-details">
                        <div class="batch-file-name">${item.name}</div>
                        <div class="batch-file-size">${formatFileSize(item.size)}</div>
                    </div>
                </div>
                <div class="batch-file-status">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                    ${item.status === 'pending' ? `<button class="btn-remove-file" onclick="removeBatchFile(${index})" title="移除">×</button>` : ''}
                </div>
            </div>
        `;
    });
    
    batchFileList.innerHTML = html;
}

// 获取状态样式类
function getStatusClass(status) {
    switch (status) {
        case 'pending': return 'status-pending';
        case 'processing': return 'status-processing';
        case 'completed': return 'status-completed';
        case 'failed': return 'status-failed';
        default: return 'status-pending';
    }
}

// 获取状态文本
function getStatusText(status) {
    switch (status) {
        case 'pending': return '等待处理';
        case 'processing': return '处理中...';
        case 'completed': return '已完成';
        case 'failed': return '处理失败';
        default: return '等待处理';
    }
}

// 移除单个文件
function removeBatchFile(index) {
    if (isBatchProcessing) {
        showError('正在处理中，无法移除文件');
        return;
    }
    
    batchFiles.splice(index, 1);
    renderBatchFileList();
    
    if (batchFiles.length === 0 && batchQueueSection) {
        batchQueueSection.style.display = 'none';
    }
}

// 开始批量处理
async function startBatchProcess() {
    if (batchFiles.length === 0) {
        showError('请先选择要处理的文件');
        return;
    }
    
    if (isBatchProcessing) {
        showError('正在处理中，请稍候');
        return;
    }
    
    isBatchProcessing = true;
    currentBatchIndex = 0;
    batchResults = [];
    
    if (batchProgressSection) {
        batchProgressSection.style.display = 'block';
    }
    
    if (batchSummarySection) {
        batchSummarySection.style.display = 'none';
    }
    
    const totalFiles = batchFiles.length;
    
    for (let i = 0; i < batchFiles.length; i++) {
        currentBatchIndex = i;
        const item = batchFiles[i];
        
        item.status = 'processing';
        renderBatchFileList();
        
        updateBatchProgress(i, totalFiles, item.name);
        
        try {
            const result = await processSingleFile(item.file);
            item.status = 'completed';
            item.result = result;
            batchResults.push({
                name: item.name,
                success: true,
                result: result
            });
        } catch (error) {
            item.status = 'failed';
            item.error = error.message;
            batchResults.push({
                name: item.name,
                success: false,
                error: error.message
            });
        }
        
        renderBatchFileList();
    }
    
    isBatchProcessing = false;
    
    updateBatchProgress(totalFiles, totalFiles, '处理完成');
    
    setTimeout(() => {
        showBatchSummary();
    }, 500);
}

// 更新批量进度
function updateBatchProgress(current, total, fileName) {
    const percent = Math.round((current / total) * 100);
    
    if (batchProgressFill) {
        batchProgressFill.style.width = percent + '%';
    }
    
    if (batchProgressPercent) {
        batchProgressPercent.textContent = percent + '%';
    }
    
    if (batchProgressText) {
        batchProgressText.textContent = `处理进度：${current} / ${total}`;
    }
    
    if (batchCurrentFile) {
        batchCurrentFile.textContent = fileName;
    }
}

// 处理单个文件
async function processSingleFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    
    const uploadResult = await uploadResponse.json();
    
    if (!uploadResult.success) {
        throw new Error(uploadResult.error || '上传失败');
    }
    
    const processResponse = await fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: uploadResult.filename })
    });
    
    const processResult = await processResponse.json();
    
    if (!processResult.success) {
        throw new Error(processResult.error || '处理失败');
    }
    
    return processResult;
}

// 显示批量结果摘要
function showBatchSummary() {
    if (batchProgressSection) {
        batchProgressSection.style.display = 'none';
    }
    
    if (batchSummarySection) {
        batchSummarySection.style.display = 'block';
    }
    
    if (!batchSummaryList) return;
    
    const successCount = batchResults.filter(r => r.success).length;
    const failCount = batchResults.filter(r => !r.success).length;
    
    let html = `
        <div class="batch-summary-header">
            <div class="summary-stat success">
                <span class="stat-number">${successCount}</span>
                <span class="stat-label">处理成功</span>
            </div>
            <div class="summary-stat failed">
                <span class="stat-number">${failCount}</span>
                <span class="stat-label">处理失败</span>
            </div>
            <div class="summary-stat total">
                <span class="stat-number">${batchResults.length}</span>
                <span class="stat-label">总计</span>
            </div>
        </div>
        <div class="batch-summary-items">
    `;
    
    batchResults.forEach((item, index) => {
        html += `
            <div class="summary-item ${item.success ? 'success' : 'failed'}">
                <div class="summary-item-icon">${item.success ? '✅' : '❌'}</div>
                <div class="summary-item-name">${item.name}</div>
                <div class="summary-item-actions">
                    ${item.success ? `<button class="btn btn-small btn-secondary" onclick="viewBatchResult(${index})">查看结果</button>` : ''}
                    ${!item.success ? `<span class="error-text">${item.error}</span>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    batchSummaryList.innerHTML = html;
    
    batchSummarySection.scrollIntoView({ behavior: 'smooth' });
}

// 查看单个批量结果
function viewBatchResult(index) {
    const item = batchResults[index];
    if (!item || !item.success) return;
    
    analysisResults = item.result;
    
    if (resultsSection) {
        resultsSection.style.display = 'block';
        displayResults(item.result);
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// 导出批量结果
function exportBatchResults() {
    if (batchResults.length === 0) {
        showError('没有可导出的结果');
        return;
    }
    
    const successResults = batchResults.filter(r => r.success);
    
    if (successResults.length === 0) {
        showError('没有成功处理的结果可导出');
        return;
    }
    
    let content = '批量分析报告\n';
    content += '=' .repeat(60) + '\n';
    content += `生成时间：${new Date().toLocaleString('zh-CN')}\n`;
    content += `成功处理：${successResults.length} 个文件\n`;
    content += '=' .repeat(60) + '\n\n';
    
    successResults.forEach((item, index) => {
        content += `\n${'─'.repeat(60)}\n`;
        content += `文件 ${index + 1}：${item.name}\n`;
        content += `${'─'.repeat(60)}\n\n`;
        content += generateSingleReport(item.result);
        content += '\n';
    });
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `批量分析报告_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.txt`;
    a.click();
    
    URL.revokeObjectURL(url);
    showSuccess('批量报告已下载');
}

// 生成单个报告内容
function generateSingleReport(result) {
    let report = '';
    const analysis = result.analysis || {};
    
    if (analysis['角色识别']) {
        const role1 = analysis['角色识别']['说话人1'] || '说话人 1';
        const role2 = analysis['角色识别']['说话人2'] || '说话人 2';
        
        report += `【${role1}】\n`;
        if (Array.isArray(result.speaker1)) {
            result.speaker1.forEach(item => {
                const text = typeof item === 'object' ? item.text : item;
                report += `${text || ''}\n`;
            });
        }
        
        report += `\n【${role2}】\n`;
        if (Array.isArray(result.speaker2)) {
            result.speaker2.forEach(item => {
                const text = typeof item === 'object' ? item.text : item;
                report += `${text || ''}\n`;
            });
        }
    }
    
    report += '\n' + '─'.repeat(40) + '\n';
    report += '分析结果\n';
    report += '─'.repeat(40) + '\n';
    
    if (analysis['客户评级']) {
        report += `\n【客户评级】\n`;
        report += `  购房意向强度: ${analysis['客户评级']['购房意向强度'] || '-'}\n`;
        report += `  综合等级: ${analysis['客户评级']['综合等级'] || '-'}\n`;
    }
    
    if (analysis['购房意向']) {
        report += `\n【购房意向】\n`;
        report += `  面积需求: ${analysis['购房意向']['面积需求'] || '未提及'}\n`;
        report += `  价格区间: ${analysis['购房意向']['价格区间'] || '未提及'}\n`;
        report += `  区域偏好: ${analysis['购房意向']['区域偏好'] || '未提及'}\n`;
    }
    
    if (analysis['总结']) {
        report += `\n【总结】\n${analysis['总结']}\n`;
    }
    
    return report;
}

// 清空批量文件
function clearBatchFiles() {
    if (isBatchProcessing) {
        showError('正在处理中，无法清空');
        return;
    }
    
    batchFiles = [];
    batchResults = [];
    
    if (batchQueueSection) {
        batchQueueSection.style.display = 'none';
    }
    
    if (batchProgressSection) {
        batchProgressSection.style.display = 'none';
    }
    
    if (batchSummarySection) {
        batchSummarySection.style.display = 'none';
    }
    
    if (fileInput) {
        fileInput.value = '';
    }
    
    renderBatchFileList();
    showSuccess('已清空文件队列');
}
