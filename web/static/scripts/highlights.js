let pasteStores = [];


const codes = document.querySelectorAll("pre > code");
for (let code of codes) {
    pasteStores.push(code.textContent);
}

hljs.highlightAll();
hljs.initLineNumbersOnLoad();