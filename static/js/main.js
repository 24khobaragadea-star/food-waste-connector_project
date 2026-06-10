// ── EXPIRY COUNTDOWN TIMERS ─────────────────────────────────
function updateTimers() {
  document.querySelectorAll('.expiry-timer[data-expiry]').forEach(el => {
    const expiry = new Date(el.dataset.expiry);
    const now = new Date();
    const diff = expiry - now;
    const span = el.querySelector('.timer-text');
    if (!span) return;

    if (diff <= 0) {
      span.textContent = 'Expired';
      el.style.color = '#dc2626';
      return;
    }

    const hours = Math.floor(diff / 3600000);
    const mins  = Math.floor((diff % 3600000) / 60000);

    if (hours < 2) {
      el.style.color = '#ea580c';
      el.style.fontWeight = '700';
    }

    if (hours < 1) {
      span.textContent = `${mins}m left`;
    } else if (hours < 24) {
      span.textContent = `${hours}h ${mins}m left`;
    } else {
      const days = Math.floor(hours / 24);
      span.textContent = `${days}d ${hours % 24}h left`;
    }
  });
}

updateTimers();
setInterval(updateTimers, 30000);

// ── AUTO-DISMISS FLASH MESSAGES ────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s, transform 0.5s';
    el.style.opacity = '0';
    el.style.transform = 'translateX(20px)';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);

// ── CONFIRM DANGEROUS ACTIONS ──────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ── MEAL ESTIMATOR (Add Food page) ─────────────────────────
const qtyInput = document.querySelector('[name="quantity"]');
const servesInput = document.querySelector('[name="serves_people"]');
if (qtyInput && servesInput) {
  qtyInput.addEventListener('input', function() {
    const text = this.value.toLowerCase();
    const match = text.match(/(\d+(\.\d+)?)\s*(kg|g|l|ml|litre|liter)/);
    if (match) {
      const val = parseFloat(match[1]);
      const unit = match[3];
      let kg = val;
      if (unit === 'g') kg = val / 1000;
      if (unit === 'l' || unit === 'litre' || unit === 'liter') kg = val;
      if (unit === 'ml') kg = val / 1000;
      const estimate = Math.round(kg * 5);
      if (estimate > 0 && !servesInput.value) {
        servesInput.value = estimate;
        servesInput.placeholder = `~${estimate} (estimated)`;
      }
    }
  });
}

// ── PREVENT PAST EXPIRY DATES ──────────────────────────────
const expiryInput = document.querySelector('[name="expiry_time"]');
if (expiryInput) {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  expiryInput.min = now.toISOString().slice(0, 16);
}
