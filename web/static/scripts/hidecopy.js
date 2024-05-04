function hideFile(button, index) {
    const pastec = document.getElementById(`__paste_c_${index}`);
    const pastea = document.getElementById(`__paste_a_${index}`);

    if (!pastec || !pastea) {
        return;
    }

    if (button.textContent == "Hide") {
        button.textContent = "Show";
        pastec.style.display = "none";
        pastea.style.flexGrow = "0";
    } else {
        button.textContent = "Hide";
        pastec.style.display = "block";
        pastea.style.flexGrow = "1";
    }
}

async function copyFile(index) {
    let button = document.getElementById(`__paste_copy_${index}`);

    if (button.textContent != "Copy") {
        button.textContent = "✓";
        return;
    }

    if (pasteStores.length == 0) {
        return
    }

    let content = pasteStores[index];
    if (!content) {
        return;
    }

    await navigator.clipboard.writeText(content);
    button.textContent = "✓";

    setTimeout(() => {
        button.textContent = "Copy";
    }, 3500);
}
