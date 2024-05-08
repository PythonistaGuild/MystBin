let pasteContainer = document.querySelector(".pasteContainer");
let count = 1;


function addFile(number) {
    let files = pasteContainer.getElementsByClassName("pasteArea");
    let currentArea = document.getElementById(`__file${number}`);

    if (currentArea.querySelector("[name='fileContent']").value) {
        currentArea.classList.remove("smallArea");
    } else if (currentArea !== files[0]) {
        currentArea.classList.add("smallArea");
    }

    if (files.length >= 5) {
        return;
    }

    for (let file of files) {
        let textArea = file.querySelector("[name='fileContent']");
        if (!textArea || !textArea.value) { return }
    }

    count += 1;

    const pasteHTML = `
    <div class="pasteArea smallArea" id="__file${count}" data-position="${count}">
        <div class="pasteHeader">
            <textarea name="fileName" class="filenameArea" rows="1" placeholder="Optional Filename..." maxlength="25"></textarea>
            <span class="deleteFile" onclick="deleteFile('__file${count}')">Delete File</span>
        </div>
        <textarea name="fileContent" required autofocus spellcheck="false" placeholder="Paste code or text..." maxlength="300000" onkeyup="addFile(${count})"></textarea>
    </div>`;

    pasteContainer.insertAdjacentHTML("beforeend", pasteHTML);
    files = pasteContainer.getElementsByClassName("pasteArea");
    if (files.length >= 5) { return }
    else if (files.length <= 2) {
        for (let file of files) {
            file.querySelector(".pasteHeader .deleteFile").classList.add("disabled");
        }
    }
    else {
        for (let file of files) {
            file.querySelector(".pasteHeader .deleteFile").classList.remove("disabled");
        }
    }
}

function deleteFile(identifier) {
    let files = pasteContainer.getElementsByClassName("pasteArea");

    if (files.length <= 2) {
        return;
    }

    let file = document.getElementById(identifier);
    file.remove();

    files = pasteContainer.getElementsByClassName("pasteArea");
    if (files.length <= 2) {
        files[0].classList.remove("smallArea");

        for (let file of files) {
            file.querySelector(".pasteHeader .deleteFile").classList.add("disabled");
        }
    }
}
