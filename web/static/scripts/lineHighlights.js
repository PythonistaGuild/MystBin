let selections = {};

function parseLines() {
    let params = new URLSearchParams(document.location.search);
    let param = params.get("lines");

    if (!param) {
        return
    }

    const regex = /F(\d+)-L(\d+)(?:-L(\d+))?/g;
    let match;
    while ((match = regex.exec(param)) !== null) {
        let file = parseInt(match[1]);
        let start = parseInt(match[2]);
        let end = match[3] ? parseInt(match[3]) : start;

        if (isNaN(file) || isNaN(start) || isNaN(end)) {
            continue;
        }

        highlightLine(null, file - 1, start);
        if (start !== end) {
            highlightLine(null, file - 1, end);
        }
    }
}

parseLines();

function removeSelected(lines) {
    lines.forEach(line => {
        let child = line.querySelector("td.lineSelected");
        if (child) {
            line.removeChild(child);
            line.classList.remove("lineNumRowSelected");
        }
    });
}

function updateParams() {
    const url = new URL(window.location);
    let param = Object.entries(selections).map(([key, value]) => {
        let end = value.end !== value.start ? `-L${value.end}_` : '';
        return `F${parseInt(key) + 1}-L${value.start}${end}`;
    }).join('');

    url.searchParams.set("lines", param);
    url.searchParams.delete("pastePassword");

    history.pushState(null, '', url);
}

function replaceSelected(lines, idIndex, index, start, end) {
    let newLines = lines.slice(start, end);
    removeSelected(newLines);

    let line = lines[index - 1];
    line.insertAdjacentHTML("beforeend", `<td class="lineSelected"></td>`);
    line.classList.add("lineNumRowSelected");

    selections[idIndex] = { "start": index, "end": index };
    updateParams();
}

function addLines(lines, idIndex, start, end) {
    let newLines = lines.slice(start - 1, end);
    newLines.forEach(line => {
        if (!line.querySelector("td.lineSelected")) {
            line.insertAdjacentHTML("beforeend", `<td class="lineSelected"></td>`);
            line.classList.add("lineNumRowSelected");
        }
    });

    selections[idIndex] = { "start": start, "end": end };
    updateParams();
}

function highlightLine(event, idI, selected) {
    let idIndex = parseInt(idI);
    let id = `__paste_c_${idIndex}`;
    let block = document.getElementById(id);

    if (!block) {
        return;
    }

    let lines = Array.from(block.querySelectorAll("tbody>tr"));
    let line = Math.min(parseInt(selected), lines.length);

    let current = selections[idIndex];
    if (!current) {
        let selectedLine = lines[line - 1];
        selectedLine.insertAdjacentHTML("beforeend", `<td class="lineSelected"></td>`);
        selectedLine.classList.add("lineNumRowSelected");

        selections[idIndex] = { "start": line, "end": line };
        updateParams();
        return;
    }

    let { start, end } = current;

    if (event && !event.shiftKey) {
        replaceSelected(lines, idIndex, line, start - 1, end);
        return;
    }

    if (!event || event.shiftKey) {
        if (line < start) {
            removeSelected(lines.slice(start, end));
            addLines(lines, idIndex, line, start);
        } else if (line <= end) {
            replaceSelected(lines, idIndex, line, start - 1, end);
        } else {
            addLines(lines, idIndex, start, line);
        }
    }
}
