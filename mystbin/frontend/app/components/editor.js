"use client";

import '@/prism/prism.css';
import {useCallback, useEffect, useLayoutEffect, useMemo, useState, Fragment} from "react";
import debounce from "lodash/debounce";
import Prism from "@/prism/prism";
import PlusSVG from "@/app/svgs/plusSVG";
import CloseSVG from "@/app/svgs/closeSVG";
import {useCookies} from "react-cookie";


const EXTENSIONS = {
    'js': 'javascript',
    'py': 'python',
    'rb': 'ruby',
    'ps1': 'powershell',
    'psm1': 'powershell',
    'sh': 'bash',
    'bat': 'batch',
    'h': 'c',
    'tex': 'latex'
};


export default function Editor({copyID, tabContent, setTabContent, fetched}) {
    const [tab, setTab] = useState(0);
    const debounceCalculate = debounce(contentHandler, 10);
    const debounceFirst = debounce(contentHandler, 100);
    const [updateHighlight, setUpdateHighlight] = useState(0);

    const textRef = useRef(null);

    useEffect(() => {
        window.Prism = window.Prism || {};
        Prism.manual = true;
    }, []);

    useLayoutEffect(() => {
        Prism.highlightAll();
    }, [updateHighlight, tab]);

    useEffect(() => {
        let count = 0;

        for (let file of tabContent) {
            let textArea = document.getElementById(`code-input-${count}`);
            textArea.textContent = file["content"];

            count += 1;
        }
    }, [fetched])

    useEffect(() => {
        Prism.highlightAll();
    }, [fetched]);

    function tabEditDown(e, index) {
        if (e.key === "Enter" || e.key === "Tab") {
            e.target.blur()
        }
    }

    function getLang(index) {
        let filename = tabContent[index].filename;
        if (filename === undefined) { return "none" }

        let extension = (/\.(\w+)$/.exec(filename) || [, 'none'])[1];
        return EXTENSIONS[extension];
    }

    function getLangFromName(name) {
        if (name === undefined) { return "none" }

        let extension = (/\.(\w+)$/.exec(name) || [, 'none'])[1];
        return EXTENSIONS[extension];
    }

    function tabEditBlur(e, index) {
        let name = e.target.innerText;

        if (name.length > 15) {
            name = name.slice(0, 15)
        } else if (name <= 0) {
            name = tabContent[index].filename
        }

        e.target.innerText = name;

        let newTabs = [...tabContent];
        newTabs[index].filename = name;
        newTabs[index].lang = getLang(index);

        setTabContent(newTabs);
        setUpdateHighlight(updateHighlight + 1);
    }

    function contentHandler() {
        setUpdateHighlight(updateHighlight + 1);
    }

    function inputChange(e, index) {
        let newTabs = [...tabContent];
        newTabs[index].content = e.target.innerText.replace(/<br ?\/?>/g, "\n");

        if (e.target.innerHTML === "" || newTabs[index].content === "") {
            newTabs[index].content = "\n"
        }

        setTabContent(newTabs);
        debounceCalculate();
    }

    function tabClicked(e, index) {
        if (index !== tab) {
            setTab(index);
        }
    }

    useEffect(() => {
        const codeInputElem = document.getElementById(`code-input-${tab}`)
        if (codeInputElem === null) {
            return
        }

        codeInputElem.focus({preventScroll: true})
    }, [tab]);

    function handleAdditionalTab() {
        // TODO: Config values...
        if (tabContent.length === 5) {
            return
        }

        let newTabs = [...tabContent];
        newTabs.push({"filename": "file.ext", "content": "\n", "lang": "none"})
        setTabContent(newTabs)
        setTab(tabContent.length)
    }

    function tabCloseClick(e, index) {
        if (tabContent.length === 1) {
            return
        }

        let newTabs = [...tabContent];
        newTabs.splice(index, 1);
        setTabContent(newTabs);

        let position

        if (tabContent.length === 1) {
            position = 0
        } else if (index + 1 >= tabContent.length) {
            position = index - 1
        } else {
            position = index
        }

        setTab(position)
        setUpdateHighlight(updateHighlight + 1)
    }

    function handlePasting(e, index) {
        e.preventDefault();

        let paste = (e.clipboardData || window.clipboardData).getData("text");

        let newTabs = [...tabContent];
        if (paste === "" && newTabs[index].content === "") {
            newTabs[index].content = "\n"
            e.target.innerText = "\n"
        }
        else {
            const selection = window.getSelection();
            if (!selection.rangeCount) {
                e.target.innerText = paste;
            }
            else {
                selection.deleteFromDocument();
                selection.getRangeAt(0).insertNode(document.createTextNode(paste));
                selection.collapseToEnd();
            }

            newTabs[index].content = e.target.innerText;
        }

        setTabContent(newTabs);
        debounceCalculate();

    }

    return (
        <>
            <div className={"tabContainer"}>
                {tabContent.map((file, index) => {
                    return <div className={index === tab ? "tabOuter tabSelected": "tabOuter tabNot"} key={`tab-${index}`}>
                        <div
                        suppressContentEditableWarning
                        className={index === tab ? "tabBase" : "tabBase tabNot"}
                        onKeyDown={(e) => tabEditDown(e, index)}
                        onBlur={(e) => tabEditBlur(e, index)}
                        onClick={(e) => tabClicked(e, index)}
                        contentEditable={tab === index}
                    >
                        {file["filename"]}
                    </div>
                        {tabContent.length > 1 ? <div onClick={(e) => tabCloseClick(e, index)} id={`tab-close-${index}`} className={"tabClose"} style={tab === index ? {display: "flex"} : null}><CloseSVG /></div> : null}
                        {index === tab ? null : <span className={"tabEmpty"}></span>}
                    </div>
                })}

                {/* TODO: Config values... */}
                {tabContent.length === 5 ? null : <span className={"tabBase tabNot tabAdd"} onClick={handleAdditionalTab}><PlusSVG /> Add</span>}
            </div>
                <pre className={"line-numbers"} style={{whiteSpace: "pre-wrap"}} suppressHydrationWarning>
                    {tabContent.map((file, index) => {
                        return (<Fragment key={`codeFrag-${index}`}>
                            <span
                                ref={textRef}
                                suppressContentEditableWarning
                                id={`code-input-${index}`}
                                key={`codeInput-${index}`}
                                className={"editorCode"}
                                inputMode={"text"}
                                onInput={e => inputChange(e, index)}
                                style={tab !== index ? {display: "none"} : null}
                                spellCheck={"false"}
                                contentEditable={true}
                                role={"textbox"}
                                onPaste={(e) => handlePasting(e, index)}
                            />
                        <code
                            id={`code-editor-${index}`}
                            key={`code-${index}`}
                            data-index-value={index}
                            className={tab !== index ? "disabledBlock" : `language-${file["lang"]}`}
                            style={tab !== index ? {display: "none"} : {userSelect: "none"}}>
                                {file["content"]}
                        </code>
                        </Fragment>)
                    })}
                </pre>
        </>
    )
}