let pasteStores = [];

const LANGUAGES = hljs.listLanguages();
let DlCount = 0;


document.addEventListener("htmx:afterRequest", function (evt) {
    if (evt.detail.xhr.status != 200) {
        return
    }

    if (evt.detail.target.id == "pastecontainer" || evt.detail.target.id == "content") {
        const HIGHLIGHT_AREAS = document.querySelectorAll(".pasteArea");

        for (let area of HIGHLIGHT_AREAS) {
            let code = area.querySelector("pre > code");
            pasteStores.push(code.textContent);

            // Highlight Code Block and get Language Details...
            let details = hljs.highlightAuto(code.textContent);
            let highlightedLang = details.language ? details.language : "plaintext";

            code.innerHTML = details.value;

            // Add Line Numbers...
            hljs.lineNumbersBlock(code, { singleLine: true });

            let header = area.querySelector(".pasteHeader");
            let langOpts = "";

            for (let lang of LANGUAGES) {
                if (lang == highlightedLang) {
                    continue
                }
                langOpts += `<option value="${lang}">${lang}</option>`
            }

            langOpts = `<option value="${highlightedLang}">${highlightedLang}</option>\n${langOpts}`
            let html = `
            <div class="langSelectContainer">
                <label>
                <input id="__lang_select_${DlCount}" list="langs" name="langSelect" placeholder="${highlightedLang}" onchange="changeLang(this, ${area.id}, ${DlCount})" /></label>
                <datalist id="langs">
                    ${langOpts}
                </datalist>
            </div>`

            header.insertAdjacentHTML("beforeend", html);
            DlCount++;
        }
    }
});


function changeLang(inp, area, index) {
    let chosen = inp.value;

    if (!chosen) { return }
    if (!LANGUAGES.includes(chosen)) { return }

    if (inp.placeholder === chosen) { return }

    let code = area.querySelector("pre > code");
    let highlighted = hljs.highlight(pasteStores[index], { language: chosen });
    code.innerHTML = highlighted.value;

    // Add Line Numbers...
    hljs.lineNumbersBlock(code, { singleLine: true });
    inp.placeholder = chosen;
}