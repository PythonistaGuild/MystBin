let pasteContainer = document.querySelector(".pasteContainer");
let count = 1;


function addFile(number) {
    let canContinue = true;
    let pasteAreas = pasteContainer.getElementsByClassName("pasteArea");
    let files = pasteContainer.querySelectorAll("[name='fileContent']");

    for (let area of pasteAreas) {
        let file = area.querySelector("[name='fileContent']");

        if (!file.value) {
            canContinue = false;

            if (file !== files[0]) {
                area.classList.add("smallArea");
            }
        }

        else if (file.value) {
            area.classList.remove("smallArea");
        }
    }

    if (!canContinue) { return }
    if (files.length === 5) { return }

    count += 1;

    const pasteHTML = `
    <div class="pasteArea smallArea" id="__file${count}" data-position="${count}" ondrop="fileDrop(event, this)" ondragover="fileDragOver(event, this)" ondragenter="fileDragStart(event, this)" ondragleave="fileDragEnd(event, this)">

        <div class="pasteHeader">
            <textarea name="fileName" class="filenameArea" rows="1" placeholder="Optional Filename..." maxlength="25"></textarea>
            <span class="deleteFile" onclick="deleteFile('__file${count}')">Delete File</span>
        </div>
        <textarea class="fileContent" name="fileContent" required autofocus spellcheck="false" placeholder="Paste code or text..." maxlength="300000" onkeyup="addFile(${count})"></textarea>
    </div>`;

    pasteContainer.insertAdjacentHTML("beforeend", pasteHTML);
}

function deleteFile(identifier) {
    let pasteAreas = pasteContainer.getElementsByClassName("pasteArea");
    let files = pasteContainer.querySelectorAll("[name='fileContent']");
    let area = document.getElementById(identifier);
    let file = area.querySelector("[name='fileContent']")

    if (pasteAreas.length == 2) {
        file.value = "";

        if (file === files[1]) {
            area.classList.add("smallArea");
        }
        return
    }

    if (files.length === 5 && file === files[4]) {
        file.value = "";
        area.classList.add("smallArea");
        return
    }

    area.remove();
    let canContinue = true;
    let newAreas = pasteContainer.getElementsByClassName("pasteArea");

    for (let newArea of newAreas) {
        let newFile = newArea.querySelector("[name='fileContent']");

        if (!newFile.value) {
            canContinue = false;

            if (newFile !== files[0]) {
                newArea.classList.add("smallArea");
            }
        }

        else if (newFile.value) {
            newArea.classList.remove("smallArea");
        }
    }

    if (!canContinue) { return }

    const pasteHTML = `
    <div class="pasteArea smallArea" id="__file${count}" data-position="${count}" ondrop="fileDrop(event, this)" ondragover="fileDragOver(event, this)" ondragenter="fileDragStart(event, this)" ondragleave="fileDragEnd(event, this)">

        <div class="pasteHeader">
            <textarea name="fileName" class="filenameArea" rows="1" placeholder="Optional Filename..." maxlength="25"></textarea>
            <span class="deleteFile" onclick="deleteFile('__file${count}')">Delete File</span>
        </div>
        <textarea class="fileContent" name="fileContent" required autofocus spellcheck="false" placeholder="Paste code or text..." maxlength="300000" onkeyup="addFile(${count})"></textarea>
    </div>`;

    pasteContainer.insertAdjacentHTML("beforeend", pasteHTML);
}
