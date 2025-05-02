/**
 * QA Report Charts
 * JavaScript for creating and animating all charts in the QA report
 * 
 * @author Tassana Khrueawan
 * @version 1.0.0
 */

document.addEventListener('DOMContentLoaded', function() {
  // Wait a bit for the DOM to be fully ready
  setTimeout(initializeCharts, 300);
});

function initializeCharts() {
  // Initialize all charts
  initLineChart();
  initDoughnutChart();
  
  // Setup chart animations on scroll
  setupChartAnimations();
}

// ====== Line Chart (Trend Analysis) ======
function initLineChart() {
  const chartCanvas = document.getElementById('order-chart');
  if (!chartCanvas) return;
  
  const ctx = chartCanvas.getContext('2d');
  
  // Create gradients
  const blueGradient = ctx.createLinearGradient(0, 0, 0, 400);
  blueGradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
  blueGradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
  
  const redGradient = ctx.createLinearGradient(0, 0, 0, 400);
  redGradient.addColorStop(0, 'rgba(244, 63, 94, 0.5)');
  redGradient.addColorStop(1, 'rgba(244, 63, 94, 0.0)');
  
  const greenGradient = ctx.createLinearGradient(0, 0, 0, 400);
  greenGradient.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
  greenGradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
  
  // Try to get chart data from the chart's data attributes
  let chartLabels = [];
  let executedData = [];
  let openedData = [];
  let closedData = [];

  try {
    chartLabels = JSON.parse(chartCanvas.dataset.labels || '["2025-02-03", "2025-02-10", "2025-02-17", "2025-02-24", "2025-03-03", "2025-03-10"]');
    executedData = JSON.parse(chartCanvas.dataset.executed || '[45, 62, 58, 45, 30, 18]');
    openedData = JSON.parse(chartCanvas.dataset.opened || '[2, 3, 4, 3, 2, 0]');
    closedData = JSON.parse(chartCanvas.dataset.closed || '[0, 1, 1, 1, 2, 3]');
  } catch (e) {
    console.error('Error parsing chart data:', e);
    // Use default data if parsing fails
    chartLabels = ["2025-02-03", "2025-02-10", "2025-02-17", "2025-02-24", "2025-03-03", "2025-03-10"];
    executedData = [45, 62, 58, 45, 30, 18];
    openedData = [2, 3, 4, 3, 2, 0];
    closedData = [0, 1, 1, 1, 2, 3];
  }
  
  // Create the chart
  const lineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartLabels,
      datasets: [
        {
          label: 'Test Cases Executed',
          data: executedData,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: blueGradient,
          borderWidth: 2,
          pointBackgroundColor: 'rgb(255, 255, 255)',
          pointBorderColor: 'rgb(59, 130, 246)',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: 'rgb(59, 130, 246)',
          pointHoverBorderColor: 'rgb(255, 255, 255)',
          tension: 0.3,
          fill: true,
        },
        {
          label: 'Defects Opened',
          data: openedData,
          borderColor: 'rgb(244, 63, 94)',
          backgroundColor: redGradient,
          borderWidth: 2,
          pointBackgroundColor: 'rgb(255, 255, 255)',
          pointBorderColor: 'rgb(244, 63, 94)',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: 'rgb(244, 63, 94)',
          pointHoverBorderColor: 'rgb(255, 255, 255)',
          tension: 0.3,
          fill: true,
        },
        {
          label: 'Defects Closed',
          data: closedData,
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: greenGradient,
          borderWidth: 2,
          pointBackgroundColor: 'rgb(255, 255, 255)',
          pointBorderColor: 'rgb(16, 185, 129)',
          pointBorderWidth: 2, 
          pointRadius: 4,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: 'rgb(16, 185, 129)',
          pointHoverBorderColor: 'rgb(255, 255, 255)',
          tension: 0.3,
          fill: true,
        },
      ]
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      hover: {
        mode: 'nearest',
        intersect: true
      },
      animations: {
        tension: {
          duration: 1000,
          easing: 'linear',
          from: 0.4,
          to: 0.3,
          loop: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          position: 'left',
          grid: {
            drawBorder: false,
            color: 'rgba(200, 200, 200, 0.2)',
          },
          ticks: {
            font: {
              size: 11
            },
            padding: 8,
            color: 'rgba(100, 100, 100, 0.8)',
          }
        },
        x: {
          grid: {
            drawBorder: false,
            display: false,
          },
          ticks: {
            font: {
              size: 11
            },
            padding: 5,
            color: 'rgba(100, 100, 100, 0.8)',
            maxRotation: 30,
            minRotation: 0
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 15,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleFont: {
            size: 13,
            weight: 'bold'
          },
          bodyFont: {
            size: 12
          },
          padding: 12,
          cornerRadius: 8,
          bodySpacing: 6,
          usePointStyle: true,
          borderColor: 'rgba(255, 255, 255, 0.3)',
          borderWidth: 1,
          boxPadding: 4,
          callbacks: {
            labelPointStyle: function(context) {
              return {
                pointStyle: 'circle',
                rotation: 0
              };
            }
          }
        }
      }
    }
  });
  
  // Store chart instance for later reference
  window.qaReportLineChart = lineChart;
  
  // Initially hide datasets for animation
  lineChart.data.datasets.forEach(dataset => {
    dataset.hidden = true;
  });
  lineChart.update();
  
  return lineChart;
}

// ====== Doughnut Chart (Test Status) ======
function initDoughnutChart() {
  const chartCanvas = document.getElementById('test-status-chart');
  if (!chartCanvas) return;
  
  const ctx = chartCanvas.getContext('2d');
  
  // Try to get chart data from the chart's data attributes
  let chartData = [];
  let chartLabels = [];

  try {
    chartData = JSON.parse(chartCanvas.dataset.values || '[50, 30, 15, 25]');
    chartLabels = JSON.parse(chartCanvas.dataset.labels || '["Passed", "Failed", "Blocked", "In Progress"]');
  } catch (e) {
    console.error('Error parsing doughnut chart data:', e);
    // Use default data if parsing fails
    chartData = [50, 30, 15, 25];
    chartLabels = ['Passed', 'Failed', 'Blocked', 'In Progress'];
  }
  
  // Create the doughnut chart
  const doughnutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: chartLabels,
      datasets: [{
        data: chartData,
        backgroundColor: [
          'rgb(16, 185, 129)', // Passed
          'rgb(244, 63, 94)',  // Failed
          'rgb(249, 115, 22)', // Blocked
          'rgb(59, 130, 246)'  // In Progress
        ],
        borderColor: 'white',
        borderWidth: 2,
        hoverBorderWidth: 0,
        hoverOffset: 10,
        borderRadius: 4,
      }]
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      cutout: '75%', // Size of center hole
      plugins: {
        legend: {
          display: false // Hide the legend
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleFont: {
            size: 13,
            weight: 'bold'
          },
          bodyFont: {
            size: 12
          },
          padding: 12,
          cornerRadius: 8,
          usePointStyle: true,
          callbacks: {
            label: function(context) {
              const value = context.raw || 0;
              const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${context.label}: ${value} (${percentage}%)`;
            }
          }
        }
      },
      animation: {
        animateScale: true,
        animateRotate: true,
        duration: 2000,
        easing: 'easeOutQuart'
      }
    }
  });
  
  // Store chart instance for later reference
  window.qaReportDoughnutChart = doughnutChart;
  
  // Animate center text
  animateCenterPercent();
  
  return doughnutChart;
}

// ====== Chart Animations ======

// Animate center percent of doughnut chart
function animateCenterPercent() {
  const centerText = document.getElementById('chart-center-percent');
  
  if (centerText) {
    // Try to get the percentage from data attribute
    const finalPercent = parseFloat(centerText.dataset.percent || '63');
    
    // Set initial text
    centerText.textContent = '0%';
    
    // Simple timeout-based animation
    setTimeout(() => {
      centerText.textContent = finalPercent + '%';
    }, 1500);
  }
}

// Animate progress bars
function animateProgressBars() {
  setTimeout(() => {
    const bars = {
      'pass-bar': 'pass-count',
      'fail-bar': 'fail-count',
      'blocked-bar': 'blocked-count',
      'progress-bar-chart': 'progress-count'
    };
    
    // For each bar, get the width from data attribute and animate
    Object.entries(bars).forEach(([barId, countId]) => {
      const bar = document.getElementById(barId);
      const count = document.getElementById(countId);
      
      if (bar) {
        const width = bar.dataset.width || '0';
        bar.style.width = width + '%';
        
        // Also update the count if present
        if (count) {
          count.textContent = bar.dataset.count || '0';
        }
      }
    });
  }, 300);
}

// Animate coverage bar
function animateCoverageBar() {
  const coverageValueText = document.getElementById('coverageValueText');
  const coverageBar = document.getElementById('coverageBar');
  
  if (coverageValueText && coverageBar) {
    const coverage = parseFloat(coverageBar.dataset.coverage || '75');
    
    coverageValueText.textContent = '0%';
    coverageBar.style.width = '0%';
    
    setTimeout(() => {
      coverageValueText.textContent = coverage + '%';
      coverageBar.style.width = coverage + '%';
    }, 500);
  }
}

// Setup chart animations on scroll
function setupChartAnimations() {
  const chartSection = document.querySelector('.lazy-chart');
  if (!chartSection || !window.qaReportLineChart) return;
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Animate the line chart when it comes into view
        window.qaReportLineChart.data.datasets.forEach((dataset, index) => {
          setTimeout(() => {
            dataset.hidden = false;
            window.qaReportLineChart.update();
          }, index * 300);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });
  
  observer.observe(chartSection);
} 