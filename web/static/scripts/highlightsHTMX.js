let pasteStores = [];


document.addEventListener("htmx:afterRequest", function (evt) {
    if (evt.detail.xhr.status != 200) {
        return
    }

    if (evt.detail.target.id == "pastecontainer" || evt.detail.target.id == "content") {
        const codes = document.querySelectorAll("pre > code");
        for (let code of codes) {
            pasteStores.push(code.textContent);
        }

        hljs.highlightAll();
        hljs.initLineNumbersOnLoad();
    }
});