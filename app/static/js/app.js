document.querySelectorAll("canvas.chart").forEach((canvas) => {
  const labels = JSON.parse(canvas.dataset.labels || "[]");
  const values = JSON.parse(canvas.dataset.values || "[]");
  if (!window.Chart || labels.length === 0) return;
  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Marks",
        data: values,
        borderColor: "#2e5fa3",
        backgroundColor: "rgba(0, 166, 223, .18)",
        tension: .35,
        fill: true
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
});

document.querySelectorAll(".alert").forEach((alert) => {
  window.setTimeout(() => {
    alert.classList.add("alert-dismissing");
    window.setTimeout(() => alert.remove(), 250);
  }, 4000);
});

const themeButton = document.querySelector("[data-theme-toggle]");
const setTheme = (theme) => {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("sms-theme", theme);
  if (themeButton) {
    themeButton.dataset.themeState = theme;
    const nextTheme = theme === "dark" ? "light" : "dark";
    themeButton.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
    themeButton.setAttribute("title", `Switch to ${nextTheme} mode`);
  }
};

setTheme(localStorage.getItem("sms-theme") || "light");
themeButton?.addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});

const closeMenus = (except) => {
  document.querySelectorAll("[data-menu-panel]").forEach((panel) => {
    if (panel !== except) panel.classList.remove("open");
  });
};

document.querySelectorAll("[data-menu-toggle]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const panel = document.querySelector(`[data-menu-panel="${button.dataset.menuToggle}"]`);
    if (!panel) return;
    const shouldOpen = !panel.classList.contains("open");
    closeMenus(panel);
    panel.classList.toggle("open", shouldOpen);
  });
});

document.addEventListener("click", () => closeMenus());
document.querySelectorAll("[data-menu-panel]").forEach((panel) => {
  panel.addEventListener("click", (event) => event.stopPropagation());
});

const signupRole = document.querySelector("[data-signup-role]");
const updateSignupFields = () => {
  const isStudent = signupRole?.value === "student";
  document.querySelectorAll(".student-signup-field").forEach((field) => {
    field.hidden = !isStudent;
    field.querySelectorAll("input").forEach((input) => {
      input.required = isStudent;
    });
  });
};

signupRole?.addEventListener("change", updateSignupFields);
updateSignupFields();
