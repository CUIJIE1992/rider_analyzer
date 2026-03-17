let gradeChart = null;
let trendChart = null;
let concernsChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initDateFilter();
    loadDashboardData();
    
    document.getElementById('applyFilter').addEventListener('click', function() {
        loadDashboardData();
    });
    
    document.getElementById('resetFilter').addEventListener('click', function() {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        loadDashboardData();
    });
});

function initDateFilter() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    document.getElementById('endDate').value = formatDate(today);
    document.getElementById('startDate').value = formatDate(thirtyDaysAgo);
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

async function loadDashboardData() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    showLoading(true);

    try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const paramsString = params.toString();

        // 并行获取所有统计数据，所有API都传递日期参数
        const [statsResponse, gradeResponse, trendResponse, concernsResponse] = await Promise.all([
            fetch(`/api/dashboard/stats?${paramsString}`),
            fetch(`/api/dashboard/grade-distribution?${paramsString}`),
            fetch(`/api/dashboard/intention-trend?${paramsString}`),
            fetch(`/api/dashboard/concerns-ranking?${paramsString}`)
        ]);
        
        if (!statsResponse.ok) {
            throw new Error('获取统计数据失败');
        }
        
        const statsData = await statsResponse.json();
        const gradeData = gradeResponse.ok ? await gradeResponse.json() : { labels: [], data: [] };
        const trendData = trendResponse.ok ? await trendResponse.json() : { labels: [], high: [], medium: [], low: [] };
        const concernsData = concernsResponse.ok ? await concernsResponse.json() : { labels: [], data: [] };
        
        // 合并所有数据
        const dashboardData = {
            ...statsData,
            grade_distribution: gradeData.labels ? 
                Object.fromEntries(gradeData.labels.map((label, i) => [label, gradeData.data[i] || 0])) :
                statsData.grade_distribution || {},
            trend_data: {
                labels: trendData.labels || [],
                values: trendData.high ? trendData.high.map((h, i) => h + (trendData.medium[i] || 0) + (trendData.low[i] || 0)) : []
            },
            concerns_ranking: concernsData.labels ? 
                concernsData.labels.map((name, i) => ({ name, count: concernsData.data[i] || 0 })) :
                []
        };
        
        updateDashboard(dashboardData);
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('加载数据失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function loadMockData() {
    const mockData = {
        total_analysis: 156,
        weekly_new: 23,
        avg_score: 72.5,
        class_a_count: 28,
        grade_distribution: {
            'A类': 28,
            'B类': 45,
            'C类': 52,
            'D类': 31
        },
        trend_data: {
            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            values: [12, 19, 15, 25, 22, 18, 23]
        },
        concerns_ranking: [
            { name: '续航能力', count: 89 },
            { name: '租金价格', count: 76 },
            { name: '换电便利', count: 65 },
            { name: '车辆性能', count: 58 },
            { name: '押金政策', count: 52 },
            { name: '保险保障', count: 45 },
            { name: '售后服务', count: 38 },
            { name: '车型选择', count: 32 }
        ],
        update_time: new Date().toLocaleString('zh-CN')
    };
    
    updateDashboard(mockData);
}

function updateDashboard(data) {
    document.getElementById('totalAnalysis').textContent = data.total_analysis || 0;
    document.getElementById('avgScore').textContent = (data.avg_score || 0).toFixed(1);
    document.getElementById('classACount').textContent = data.class_a_count || 0;
    // 使用当前时间作为数据更新时间
    document.getElementById('updateTime').textContent = new Date().toLocaleString('zh-CN');
    
    renderGradeChart(data.grade_distribution || {});
    renderTrendChart(data.trend_data || { labels: [], values: [] });
    renderConcernsChart(data.concerns_ranking || []);
}

function renderGradeChart(gradeData) {
    const ctx = document.getElementById('gradeChart').getContext('2d');
    
    if (gradeChart) {
        gradeChart.destroy();
    }
    
    const labels = Object.keys(gradeData);
    const values = Object.values(gradeData);
    
    const colors = {
        'A类': '#10b981',
        'B类': '#3b82f6',
        'C类': '#f59e0b',
        'D类': '#ef4444'
    };
    
    const backgroundColors = labels.map(label => colors[label] || '#6b7280');
    
    gradeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderTrendChart(trendData) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.labels,
            datasets: [{
                label: '分析数量',
                data: trendData.values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

function renderConcernsChart(concernsData) {
    const ctx = document.getElementById('concernsChart').getContext('2d');
    
    if (concernsChart) {
        concernsChart.destroy();
    }
    
    const labels = concernsData.map(item => item.name);
    const values = concernsData.map(item => item.count);
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.3)');
    
    concernsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '提及次数',
                data: values,
                backgroundColor: gradient,
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `提及次数: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 13
                        }
                    }
                }
            }
        }
    });
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.style.display = 'flex';
    } else {
        overlay.style.display = 'none';
    }
}

function showError(message) {
    // 创建错误提示元素
    let errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
        `;
        document.body.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}
