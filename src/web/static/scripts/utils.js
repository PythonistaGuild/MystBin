function getLangByName(name) {
    splat = name.split(".");
    if (splat.length <= 1) {
        return null
    }

    ext = splat[splat.length - 1];
    lang = hljs.getLanguage(ext);

    if (!lang) {
        return null
    }

    let lname = lang.name.replace(/\s+/g, '').toLowerCase();
    let lastN = lname.split(",")[0];
    return lastN;
}