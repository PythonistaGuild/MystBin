function calculateSettingAsThemeString({
    localStorageTheme,
    systemSettingDark,
}) {
    if (localStorageTheme !== null) {
        return localStorageTheme;
    }

    if (systemSettingDark.matches) {
        return "dark";
    }

    return "light";
}

function updateThemeOnHtmlEl({ theme }) {
    document.querySelector("html").setAttribute("data-theme", theme);
}

let localStorageTheme = localStorage.getItem("theme");
let systemSettingDark = window.matchMedia("(prefers-color-scheme: dark)");

let currentThemeSetting = calculateSettingAsThemeString({
    localStorageTheme,
    systemSettingDark,
});

updateThemeOnHtmlEl({ theme: currentThemeSetting });