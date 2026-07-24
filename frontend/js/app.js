// LevelUpLife Frontend App Logic

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  let currentUser = null;
  let habits = [];
  let heatmapData = [];
  let selectedCategory = 'ALL';

  // DOM Elements
  const authView = document.getElementById('auth-view');
  const dashboardView = document.getElementById('dashboard-view');
  const navUserBar = document.getElementById('nav-user-bar');
  const toastContainer = document.getElementById('toast-container');
  const toastMessage = document.getElementById('toast-message');

  // User Header Elements
  const userLevel = document.getElementById('user-level');
  const userXpBar = document.getElementById('user-xp-bar');
  const userCoins = document.getElementById('user-coins');
  const userName = document.getElementById('user-name');
  const logoutBtn = document.getElementById('logout-btn');

  // Auth Elements
  const tabLogin = document.getElementById('tab-login');
  const tabSignup = document.getElementById('tab-signup');
  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');

  // Stats Elements
  const statTotalHabits = document.getElementById('stat-total-habits');
  const statDoneToday = document.getElementById('stat-done-today');
  const statBestStreak = document.getElementById('stat-best-streak');
  const statTotalXp = document.getElementById('stat-total-xp');

  // Habits Elements
  const habitList = document.getElementById('habit-list');
  const emptyHabitsMsg = document.getElementById('empty-habits-msg');
  const addHabitBtn = document.getElementById('add-habit-btn');
  const categoryFilter = document.getElementById('category-filter');

  // Heatmap Element
  const heatmapGrid = document.getElementById('heatmap-grid');

  // Modals
  const habitModal = document.getElementById('habit-modal');
  const habitModalTitle = document.getElementById('habit-modal-title');
  const habitForm = document.getElementById('habit-form');
  const habitIdInput = document.getElementById('habit-id');
  const habitTitleInput = document.getElementById('habit-title-input');
  const habitCategoryInput = document.getElementById('habit-category-input');
  const closeHabitModalBtn = document.getElementById('close-habit-modal');

  const dateModal = document.getElementById('date-modal');
  const dateModalTitle = document.getElementById('date-modal-title');
  const dateModalRate = document.getElementById('date-modal-rate');
  const dateModalHabitsList = document.getElementById('date-modal-habits-list');
  const closeDateModalBtn = document.getElementById('close-date-modal');

  const victoryModal = document.getElementById('victory-modal');
  const closeVictoryModalBtn = document.getElementById('close-victory-modal');

  // Theme Elements
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeIcon = document.getElementById('theme-icon');
  const themeText = document.getElementById('theme-text');

  // --- INITIALIZATION ---
  initApp();

  async function initApp() {
    // Read and apply saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    setupEventListeners();
    const token = ApiService.getToken();
    if (token) {
      try {
        currentUser = await ApiService.getMe();
        showDashboard();
      } catch (err) {
        showToast("Session expired. Please log in again.", "error");
        showAuthView();
      }
    } else {
      showAuthView();
    }
  }

  // --- THEME MANAGEMENT ---
  function applyTheme(theme) {
    if (theme === 'light') {
      document.body.classList.add('light-mode');
      if (themeIcon) themeIcon.textContent = '🌙';
      if (themeText) themeText.textContent = 'DARK';
      localStorage.setItem('theme', 'light');
    } else {
      document.body.classList.remove('light-mode');
      if (themeIcon) themeIcon.textContent = '☀️';
      if (themeText) themeText.textContent = 'LIGHT';
      localStorage.setItem('theme', 'dark');
    }
  }

  function toggleTheme() {
    const isLight = document.body.classList.contains('light-mode');
    applyTheme(isLight ? 'dark' : 'light');
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    // Theme Toggle
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', toggleTheme);
    }

    // Auth Tabs
    tabLogin.addEventListener('click', () => switchAuthTab('login'));
    tabSignup.addEventListener('click', () => switchAuthTab('signup'));

    // Auth Submit
    loginForm.addEventListener('submit', handleLogin);
    signupForm.addEventListener('submit', handleSignup);
    logoutBtn.addEventListener('click', handleLogout);

    // Filter & Add Habit
    categoryFilter.addEventListener('change', (e) => {
      selectedCategory = e.target.value;
      renderHabits();
    });

    addHabitBtn.addEventListener('click', () => openHabitModal());
    closeHabitModalBtn.addEventListener('click', closeHabitModal);
    habitForm.addEventListener('submit', handleHabitFormSubmit);

    // Modals Close
    closeDateModalBtn.addEventListener('click', () => dateModal.classList.add('hidden'));
    closeVictoryModalBtn.addEventListener('click', () => victoryModal.classList.add('hidden'));

    // Expired Session Event
    window.addEventListener('auth_expired', () => {
      showToast("Authentication required. Logged out.", "error");
      showAuthView();
    });
  }

  // --- VIEW SWITCHING ---
  function showAuthView() {
    authView.classList.remove('hidden');
    dashboardView.classList.add('hidden');
    navUserBar.classList.add('hidden');
  }

  async function showDashboard() {
    authView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
    navUserBar.classList.remove('hidden');

    updateUserHeader();
    await loadHabits();
    await loadHeatmap();
  }

  function switchAuthTab(tab) {
    if (tab === 'login') {
      tabLogin.className = "flex-1 py-2 text-center text-yellow-400 border-b-4 border-yellow-400 font-bold";
      tabSignup.className = "flex-1 py-2 text-center text-gray-400 hover:text-white";
      loginForm.classList.remove('hidden');
      signupForm.classList.add('hidden');
    } else {
      tabSignup.className = "flex-1 py-2 text-center text-yellow-400 border-b-4 border-yellow-400 font-bold";
      tabLogin.className = "flex-1 py-2 text-center text-gray-400 hover:text-white";
      signupForm.classList.remove('hidden');
      loginForm.classList.add('hidden');
    }
  }

  // --- TOAST NOTIFICATIONS ---
  function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    toastMessage.className = type === 'error' ? 'text-red-400' : (type === 'success' ? 'text-green-400' : 'text-yellow-400');
    toastContainer.classList.remove('hidden');

    setTimeout(() => {
      toastContainer.classList.add('hidden');
    }, 4000);
  }

  // --- AUTH HANDLERS ---
  async function handleLogin(e) {
    e.preventDefault();
    const usernameOrEmail = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    try {
      const res = await ApiService.login(usernameOrEmail, password);
      currentUser = res.user;
      showToast(`Welcome back, ${currentUser.username}!`, 'success');
      showDashboard();
    } catch (err) {
      showToast(err.message || "Login failed", 'error');
    }
  }

  async function handleSignup(e) {
    e.preventDefault();
    const username = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;

    try {
      const res = await ApiService.signup(username, email, password);
      currentUser = res.user;
      showToast(`Player ${currentUser.username} created! +100 Coins Bonus!`, 'success');
      showDashboard();
    } catch (err) {
      showToast(err.message || "Signup failed", 'error');
    }
  }

  function handleLogout() {
    ApiService.removeToken();
    currentUser = null;
    showToast("Logged out successfully.", "info");
    showAuthView();
  }

  // --- USER HEADER UPDATE ---
  function updateUserHeader() {
    if (!currentUser) return;

    userLevel.textContent = currentUser.level;
    userCoins.textContent = currentUser.coins;
    userName.textContent = currentUser.username.toUpperCase();

    // Calculate XP progress percentage (0 to 100)
    const xpIntoLevel = currentUser.total_xp % 100;
    userXpBar.style.width = `${xpIntoLevel}%`;

    // Stats Bar
    statTotalXp.textContent = currentUser.total_xp;
  }

  // --- HABITS DATA & RENDER ---
  async function loadHabits() {
    try {
      habits = await ApiService.getHabits();
      renderHabits();
    } catch (err) {
      showToast("Failed to load habits", "error");
    }
  }

  function renderHabits() {
    habitList.innerHTML = '';

    const filtered = selectedCategory === 'ALL' 
      ? habits 
      : habits.filter(h => h.category === selectedCategory);

    if (filtered.length === 0) {
      emptyHabitsMsg.classList.remove('hidden');
    } else {
      emptyHabitsMsg.classList.add('hidden');
    }

    let doneTodayCount = 0;
    let maxStreak = 0;

    filtered.forEach(h => {
      if (h.completed_today) doneTodayCount++;
      if (h.current_streak > maxStreak) maxStreak = h.current_streak;

      const card = document.createElement('div');
      card.className = `nes-container is-dark p-3 sm:p-4 flex flex-wrap items-center justify-between gap-3 sm:gap-4 border-2 ${
        h.completed_today ? 'border-green-500 bg-gray-900/80' : 'border-gray-700'
      }`;

      const categoryColors = {
        Health: 'is-error',
        Coding: 'is-primary',
        Fitness: 'is-warning',
        Mindset: 'is-success',
        General: 'is-dark'
      };

      const categoryClass = categoryColors[h.category] || 'is-dark';

      card.innerHTML = `
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <button class="toggle-btn nes-btn text-xs ${h.completed_today ? 'is-success' : 'is-normal'} shrink-0" data-id="${h.id}">
            ${h.completed_today ? '✓ DONE' : 'DO IT'}
          </button>

          <div class="min-w-0 flex-1 break-words">
            <h3 class="text-xs sm:text-sm font-bold text-white break-words ${h.completed_today ? 'line-through text-gray-400' : ''}">${escapeHtml(h.title)}</h3>
            <div class="flex flex-wrap items-center gap-2 mt-1">
              <span class="nes-badge"><span class="${categoryClass} text-[10px] py-0 px-1">${escapeHtml(h.category)}</span></span>
              <span class="text-[10px] text-red-400 font-bold">🔥 ${h.current_streak} DAY${h.current_streak === 1 ? '' : 'S'}</span>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2 habit-card-actions">
          ${
            !h.completed_today ? `
              <button class="revive-btn nes-btn is-warning text-[10px] py-1 px-2" data-id="${h.id}" title="Spend 20 coins to keep/restore streak">
                REVIVE 🪙20
              </button>
            ` : ''
          }
          <button class="edit-btn nes-btn is-primary text-[10px] py-1 px-2" data-id="${h.id}">EDIT</button>
          <button class="delete-btn nes-btn is-error text-[10px] py-1 px-2" data-id="${h.id}">DEL</button>
        </div>
      `;

      habitList.appendChild(card);
    });

    // Update Summary Cards
    statTotalHabits.textContent = habits.length;
    statDoneToday.textContent = doneTodayCount;
    statBestStreak.textContent = `${maxStreak} 🔥`;

    // Attach Event Handlers
    document.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => handleToggleHabit(btn.getAttribute('data-id')));
    });

    document.querySelectorAll('.revive-btn').forEach(btn => {
      btn.addEventListener('click', () => handleReviveHabit(btn.getAttribute('data-id')));
    });

    document.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', () => handleEditHabit(btn.getAttribute('data-id')));
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', () => handleDeleteHabit(btn.getAttribute('data-id')));
    });
  }

  // --- HABIT ACTIONS ---
  async function handleToggleHabit(id) {
    try {
      const res = await ApiService.toggleHabit(id);
      currentUser = res.user_stats;
      updateUserHeader();

      showToast(
        res.completed 
          ? `+${res.xp_gained} XP, +${res.coins_gained} Coins!` 
          : "Quest toggled off.", 
        res.completed ? "success" : "info"
      );

      await loadHabits();
      await loadHeatmap();

      // Trigger VICTORY MODAL when ALL completed today!
      if (res.all_completed) {
        victoryModal.classList.remove('hidden');
      }
    } catch (err) {
      showToast(err.message || "Failed to toggle habit", "error");
    }
  }

  async function handleReviveHabit(id) {
    if (currentUser.coins < 20) {
      showToast("Not enough coins! Need 20 coins to revive.", "error");
      return;
    }

    try {
      const res = await ApiService.reviveHabit(id);
      currentUser.coins = res.coins_remaining;
      updateUserHeader();

      showToast("Streak Revived! -20 Coins.", "success");
      await loadHabits();
      await loadHeatmap();
    } catch (err) {
      showToast(err.message || "Failed to revive streak", "error");
    }
  }

  function openHabitModal(habit = null) {
    if (habit) {
      habitModalTitle.textContent = "EDIT QUEST";
      habitIdInput.value = habit.id;
      habitTitleInput.value = habit.title;
      habitCategoryInput.value = habit.category;
    } else {
      habitModalTitle.textContent = "NEW QUEST";
      habitIdInput.value = "";
      habitTitleInput.value = "";
      habitCategoryInput.value = "General";
    }
    habitModal.classList.remove('hidden');
  }

  function closeHabitModal() {
    habitModal.classList.add('hidden');
  }

  function handleEditHabit(id) {
    const target = habits.find(h => h.id == id);
    if (target) {
      openHabitModal(target);
    }
  }

  async function handleDeleteHabit(id) {
    if (!confirm("Are you sure you want to abandon this quest?")) return;

    try {
      await ApiService.deleteHabit(id);
      showToast("Quest deleted.", "info");
      await loadHabits();
      await loadHeatmap();
    } catch (err) {
      showToast(err.message || "Failed to delete habit", "error");
    }
  }

  async function handleHabitFormSubmit(e) {
    e.preventDefault();
    const id = habitIdInput.value;
    const title = habitTitleInput.value.trim();
    const category = habitCategoryInput.value;

    try {
      if (id) {
        await ApiService.updateHabit(id, title, category, "daily");
        showToast("Quest updated!", "success");
      } else {
        await ApiService.createHabit(title, category, "daily");
        showToast("New Quest added!", "success");
      }
      closeHabitModal();
      await loadHabits();
    } catch (err) {
      showToast(err.message || "Failed to save quest", "error");
    }
  }

  // --- HEATMAP MATRIX ---
  async function loadHeatmap() {
    try {
      heatmapData = await ApiService.getHeatmap();
      renderHeatmap();
    } catch (err) {
      console.error("Heatmap load error:", err);
    }
  }

  function renderHeatmap() {
    heatmapGrid.innerHTML = '';

    heatmapData.forEach(item => {
      const cell = document.createElement('div');
      cell.className = `heatmap-cell level-${item.level}`;
      cell.title = `${item.date}: ${item.count} quests completed`;
      cell.setAttribute('data-date', item.date);

      cell.addEventListener('click', () => openDateStatsModal(item.date));
      heatmapGrid.appendChild(cell);
    });
  }

  async function openDateStatsModal(dateStr) {
    try {
      const data = await ApiService.getDayStats(dateStr);
      dateModalTitle.textContent = `STATS: ${dateStr}`;
      dateModalRate.textContent = `${data.completion_rate}% (${data.completed_habits}/${data.total_habits})`;

      dateModalHabitsList.innerHTML = '';
      if (data.habits.length === 0) {
        dateModalHabitsList.innerHTML = '<p class="text-gray-500 italic">No active habits recorded on this date.</p>';
      } else {
        data.habits.forEach(h => {
          const item = document.createElement('div');
          item.className = 'flex justify-between items-center bg-gray-800 p-2 border border-gray-700 rounded text-[10px]';
          item.innerHTML = `
            <span>${escapeHtml(h.title)}</span>
            <span class="${h.completed_today ? 'text-green-400' : 'text-red-400'} font-bold">
              ${h.completed_today ? '✓ COMPLETED' : '❌ MISSED/SKIPPED'}
            </span>
          `;
          dateModalHabitsList.appendChild(item);
        });
      }

      dateModal.classList.remove('hidden');
    } catch (err) {
      showToast("Failed to fetch date stats", "error");
    }
  }

  // Helper XSS prevention
  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
