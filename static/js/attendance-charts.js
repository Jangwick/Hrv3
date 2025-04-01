/**
 * Chart creation functions for attendance analytics
 */

/**
 * Create stacked bar chart for attendance distribution
 */
function createAttendanceChart(canvasId, labels, presentData, lateData, excusedData, absentData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Clean up any existing chart
    if (window.attendanceDistributionChart) {
        window.attendanceDistributionChart.destroy();
    }
    
    // Create new chart
    window.attendanceDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Present',
                    data: presentData,
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    borderColor: 'rgb(40, 167, 69)',
                    borderWidth: 1
                },
                {
                    label: 'Late',
                    data: lateData,
                    backgroundColor: 'rgba(0, 123, 255, 0.8)',
                    borderColor: 'rgb(0, 123, 255)',
                    borderWidth: 1
                },
                {
                    label: 'Excused',
                    data: excusedData,
                    backgroundColor: 'rgba(255, 193, 7, 0.8)',
                    borderColor: 'rgb(255, 193, 7)',
                    borderWidth: 1
                },
                {
                    label: 'Absent',
                    data: absentData,
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderColor: 'rgb(220, 53, 69)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Attendance Distribution by Month'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Records'
                    }
                }
            }
        }
    });
    
    return window.attendanceDistributionChart;
}

/**
 * Create line chart for attendance trends
 */
function createAttendanceTrendChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Clean up any existing chart
    if (window.attendanceTrendChart) {
        window.attendanceTrendChart.destroy();
    }
    
    // Create gradient
    const gradientFill = ctx.createLinearGradient(0, 0, 0, 400);
    gradientFill.addColorStop(0, 'rgba(0, 123, 255, 0.7)');
    gradientFill.addColorStop(1, 'rgba(0, 123, 255, 0.1)');
    
    // Create new chart
    window.attendanceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Attendance Rate %',
                    data: data,
                    fill: true,
                    backgroundColor: gradientFill,
                    borderColor: 'rgb(0, 123, 255)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgb(0, 123, 255)',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Attendance Rate Trend'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Rate: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: Math.max(0, Math.min(...data) - 10),
                    max: 100,
                    title: {
                        display: true,
                        text: 'Rate (%)'
                    }
                }
            }
        }
    });
    
    return window.attendanceTrendChart;
}

/**
 * Create horizontal bar chart for department comparison
 */
function createUnitComparisonChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Clean up any existing chart
    if (window.unitComparisonChart) {
        window.unitComparisonChart.destroy();
    }
    
    // Create color array based on rate values
    const bgColors = data.map(value => {
        if (value >= 90) return 'rgba(40, 167, 69, 0.8)'; // Green for high attendance
        if (value >= 80) return 'rgba(0, 123, 255, 0.8)'; // Blue for good attendance
        if (value >= 70) return 'rgba(255, 193, 7, 0.8)'; // Yellow for medium attendance
        return 'rgba(220, 53, 69, 0.8)'; // Red for low attendance
    });
    
    // Create new chart
    window.unitComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Attendance Rate',
                    data: data,
                    backgroundColor: bgColors,
                    borderWidth: 1
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Attendance Rate by Department'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Rate: ${context.parsed.x}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Rate (%)'
                    }
                }
            }
        }
    });
    
    return window.unitComparisonChart;
}
