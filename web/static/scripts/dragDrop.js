let dragCounter = 0;

function fileDragStart(event, target) {
    event.preventDefault();
    event.stopPropagation();

    target.classList.add("dragging");
    let pasteAreas = pasteContainer.getElementsByClassName("pasteArea");

    for (let area of pasteAreas) {
        if (area === target) {
            continue;
        }
        area.classList.remove("dragging");
    }

    if (target.classList.contains("smallArea")) {
        target.classList.remove("smallArea");
    }

    dragCounter++;
}

function fileDragOver(event, target) {
    event.preventDefault();

    if (event.dataTransfer.items === 0) { return }

    let type = event.dataTransfer.items[0].type;
    if (!type) { return }

    if (!type.startsWith("text/") && !type.startsWith("application/")) {
        target.classList.add("prevented");
        event.dataTransfer.dropEffect = "none";
    }
}

function fileDragEnd(event, target) {
    event.preventDefault();
    event.stopPropagation();

    dragCounter--;
    if (dragCounter !== 0) { return }

    target.classList.remove("dragging");
    target.classList.remove("prevented");

}

async function fileDrop(event, target) {
    event.preventDefault();
    event.stopPropagation();

    dragCounter = 0;

    target.classList.remove("prevented");
    target.classList.remove("dragging");

    const file = event.dataTransfer.files[0];
    const textArea = target.querySelector(".fileContent");
    const fileName = target.querySelector(".pasteHeader > .filenameArea");

    // Allow double the server limit incase of editing...
    if (file.size > 600000) {
        return;
    }

    if (!file.type) { }
    else if (!file.type.startsWith("text/") && !file.type.startsWith("application/")) {
        return;
    }

    let name = file.name;
    let content = await file.text();
    fileName.value = name;
    textArea.value = content;

    addFile();
}