/**
 * main.js - เป็นไฟล์หลักสำหรับ QA Report Dashboard
 * @version 1.0.0
 * @author QA Automate
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all components
  initSidebar();
  initDropdowns();
  initDateRangePicker();
  initScrollEffects();
  
  // Dark mode toggle
  initDarkMode();
  
  // Filter functionality for tables
  initTableFilters();
});

/**
 * Initialize sidebar toggling
 */
function initSidebar() {
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content');
  
  if (!sidebarToggle || !sidebar || !mainContent) return;
  
  sidebarToggle.addEventListener('click', function() {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    
    // Store sidebar state in localStorage
    const isSidebarCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isSidebarCollapsed);
  });
  
  // Restore sidebar state from localStorage
  const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (isSidebarCollapsed) {
    sidebar.classList.add('collapsed');
    mainContent.classList.add('expanded');
  }
}

/**
 * Initialize dropdown menus
 */
function initDropdowns() {
  const dropdowns = document.querySelectorAll('.dropdown');
  
  dropdowns.forEach(dropdown => {
    const trigger = dropdown.querySelector('.dropdown-trigger');
    const menu = dropdown.querySelector('.dropdown-menu');
    
    if (!trigger || !menu) return;
    
    trigger.addEventListener('click', function(e) {
      e.stopPropagation();
      
      // Close all other dropdowns
      dropdowns.forEach(otherDropdown => {
        if (otherDropdown !== dropdown) {
          otherDropdown.querySelector('.dropdown-menu')?.classList.remove('open');
        }
      });
      
      menu.classList.toggle('open');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
      menu.classList.remove('open');
    });
    
    // Prevent dropdown from closing when clicking inside it
    menu.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  });
}

/**
 * Initialize date range picker
 */
function initDateRangePicker() {
  const dateRangePicker = document.getElementById('date-range-picker');
  
  if (!dateRangePicker) return;
  
  // Check if flatpickr is available
  if (typeof flatpickr === 'function') {
    flatpickr(dateRangePicker, {
      mode: 'range',
      dateFormat: 'Y-m-d',
      defaultDate: [
        new Date(Date.now() - 14 * 24 * 60 * 60 * 1000), // 14 days ago
        new Date()
      ],
      onChange: function(selectedDates) {
        if (selectedDates.length === 2) {
          // Update report date range display
          const startDate = formatDate(selectedDates[0]);
          const endDate = formatDate(selectedDates[1]);
          updateDateRangeDisplay(startDate, endDate);
          
          // Optional: trigger report data refresh
          refreshReportData(startDate, endDate);
        }
      }
    });
  } else {
    // Fallback to native date inputs if flatpickr not available
    dateRangePicker.type = 'date';
    dateRangePicker.valueAsDate = new Date();
  }
}

/**
 * Initialize scroll effects
 */
function initScrollEffects() {
  const scrollElements = document.querySelectorAll('.scroll-reveal');
  
  const elementInView = (el, dividend = 1) => {
    const elementTop = el.getBoundingClientRect().top;
    return (
      elementTop <= (window.innerHeight || document.documentElement.clientHeight) / dividend
    );
  };
  
  const elementOutOfView = (el) => {
    const elementTop = el.getBoundingClientRect().top;
    return (
      elementTop > (window.innerHeight || document.documentElement.clientHeight)
    );
  };
  
  const displayScrollElement = (element) => {
    element.classList.add('scrolled');
  };
  
  const hideScrollElement = (element) => {
    element.classList.remove('scrolled');
  };
  
  const handleScrollAnimation = () => {
    scrollElements.forEach((el) => {
      if (elementInView(el, 1.25)) {
        displayScrollElement(el);
      } else if (elementOutOfView(el)) {
        hideScrollElement(el);
      }
    });
  };
  
  window.addEventListener('scroll', () => {
    handleScrollAnimation();
  });
  
  // Initialize all elements on page load
  handleScrollAnimation();
}

/**
 * Initialize dark mode toggle
 */
function initDarkMode() {
  const darkModeToggle = document.getElementById('dark-mode-toggle');
  const htmlElement = document.documentElement;
  
  if (!darkModeToggle) return;
  
  // Check for saved user preference and system preference
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  // Apply saved preference or system preference
  if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    htmlElement.setAttribute('data-theme', 'dark');
    darkModeToggle.checked = true;
  } else {
    htmlElement.setAttribute('data-theme', 'light');
    darkModeToggle.checked = false;
  }
  
  // Handle toggle click
  darkModeToggle.addEventListener('change', function() {
    if (this.checked) {
      htmlElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      htmlElement.setAttribute('data-theme', 'light');
      localStorage.setItem('theme', 'light');
    }
  });
}

/**
 * Initialize table filters
 */
function initTableFilters() {
  const tableFilters = document.querySelectorAll('.table-filter');
  
  tableFilters.forEach(filter => {
    const targetTable = document.querySelector(filter.dataset.target);
    const searchInput = filter.querySelector('input[type="search"]');
    
    if (!targetTable || !searchInput) return;
    
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const rows = targetTable.querySelectorAll('tbody tr');
      
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const display = text.includes(searchTerm) ? '' : 'none';
        row.style.display = display;
      });
      
      // Show "no results" message if all rows are hidden
      const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
      const noResultsMsg = targetTable.querySelector('.no-results-message');
      
      if (visibleRows.length === 0) {
        if (!noResultsMsg) {
          const tbody = targetTable.querySelector('tbody');
          const messageTr = document.createElement('tr');
          messageTr.className = 'no-results-message';
          messageTr.innerHTML = `<td colspan="100%" class="text-center">ไม่พบข้อมูลที่ค้นหา "${searchTerm}"</td>`;
          tbody.appendChild(messageTr);
        }
      } else if (noResultsMsg) {
        noResultsMsg.remove();
      }
    });
  });
}

/**
 * Helper function to format date
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string (YYYY-MM-DD)
 */
function formatDate(date) {
  return date.toISOString().split('T')[0];
}

/**
 * Update the date range display in the UI
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 */
function updateDateRangeDisplay(startDate, endDate) {
  const dateRangeDisplay = document.getElementById('date-range-display');
  if (dateRangeDisplay) {
    dateRangeDisplay.textContent = `${startDate} ถึง ${endDate}`;
  }
}

/**
 * Refreshes report data based on selected date range
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 */
function refreshReportData(startDate, endDate) {
  console.log(`Refreshing report data for range: ${startDate} to ${endDate}`);
  // Implementation would depend on how data is loaded
  // This could trigger AJAX requests or redraw charts
  
  // Example: update charts if they exist
  if (typeof refreshCharts === 'function') {
    refreshCharts(startDate, endDate);
  }
} 