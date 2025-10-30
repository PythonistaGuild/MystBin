let pasteContainer = document.querySelector(".pasteContainer");
let addButton = document.querySelector(".addPaste");
let count = 0;

addButton.addEventListener("click", (e) => {
    let files = pasteContainer.getElementsByClassName("pasteArea");

    if (files.length >= 5) {
        return;
    }

    count += 1;

    const pasteHTML = `<div class="pasteArea" id="__file${count}">
<div class="pasteHeader">
  <textarea name="fileName" class="filenameArea" rows="1" placeholder="Optional Filename..." maxlength="25"></textarea>
  <span class="deleteFile" onclick="deleteFile('__file${count}')">Delete File</span>
</div>
<textarea name="fileContent" required autofocus spellcheck="false" placeholder="Paste code or text..." maxlength="300000"></textarea>
</div>`;

    pasteContainer.insertAdjacentHTML("beforeend", pasteHTML);

    files = pasteContainer.getElementsByClassName("pasteArea");
    for (let file of files) {
        file.querySelector(".pasteHeader .deleteFile").classList.remove("disabled");
    }

    if (files.length >= 5) {
        addButton.style.display = "none";
    }
});

function deleteFile(identifier) {
    let files = pasteContainer.getElementsByClassName("pasteArea");

    if (files.length == 1) {
        return;
    } else {
        addButton.style.display = "flex";
    }

    document.getElementById(identifier).remove();

    files = pasteContainer.getElementsByClassName("pasteArea");
    if (files.length == 1) {
        files[0]
            .querySelector(".pasteHeader .deleteFile")
            .classList.add("disabled");
    }
}
