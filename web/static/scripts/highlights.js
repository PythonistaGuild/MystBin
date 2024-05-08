let pasteStores = [];

hljs.highlightAll();
hljs.initLineNumbersOnLoad();

window.onload = (e) => {
    const codes = document.querySelectorAll("pre > code");
    for (let code of codes) {
        pasteStores.push(code.textContent);
    }
}