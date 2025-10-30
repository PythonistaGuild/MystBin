function updateButton({ checkboxEl, isDark }) {
  checkboxEl.checked = isDark ? true : false;
}

let checkbox = document.querySelector("#themeSwitch");
updateButton({ checkboxEl: checkbox, isDark: currentThemeSetting === "dark" });

checkbox.addEventListener("click", (event) => {
  const newTheme = currentThemeSetting === "dark" ? "light" : "dark";

  localStorage.setItem("theme", newTheme);
  updateButton({ checkboxEl: checkbox, isDark: newTheme === "dark" });
  updateThemeOnHtmlEl({ theme: newTheme });

  currentThemeSetting = newTheme;
});
