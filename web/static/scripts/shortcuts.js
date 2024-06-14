window.addEventListener("keydown", (e) => {

    // Ctrl + s === Save Paste
    if (e.ctrlKey && e.key === "s") {
        e.preventDefault();
        e.stopPropagation();
        return;
    }

    // Ctrl + Shift + R === Raw Paste
    else if (e.ctrlKey && e.shiftKey && e.key === "R") {
        e.preventDefault();
        e.stopPropagation();
        return;
    }
});