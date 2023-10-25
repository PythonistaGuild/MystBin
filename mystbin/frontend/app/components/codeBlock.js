"use client";

import Prism from "@/prism/prism.js";
import {Fragment, useEffect, useLayoutEffect, useState} from "react";
import CopySVG from "@/app/svgs/copySVG";
import DoneSVG from "@/app/svgs/doneSVG";
import CloseSVG from "@/app/svgs/closeSVG";

// WE ONLY WANT SPECIFIC LANGUAGES NOT 192 ...
import hljs from 'highlight.js'
const supportedLangs = [
    'javascript',
    'python',
    'ruby',
    'powershell',
    'bash',
    'c',
    'cpp',
    'c++',
    'd',
    'xml',
    'html',
    'json',
    'java',
    'lua',
    'rust',
    'yaml',
    'css'
]


const EXTENSIONS = {
    'js': 'javascript',
    'py': 'python',
    'rb': 'ruby',
    'ps1': 'powershell',
    'sh': 'bash',
    'bat': 'batch',
    'h': 'c',
    'tex': 'latex'
};


export default function CodeBlock({children}) {
    const [tab, setTab] = useState(0);
    const [tabContent, setTabContent] = useState([]);
    const [copiedContent, setCopiedContent] = useState(null);

    useEffect(() => {
        let files = [];

        for (let file of children) {
            let extension = (/\.(\w+)$/.exec(file["filename"]) || [, 'none'])[1];
            // TODO: Add extensions for all supported langs...
            let lang = EXTENSIONS[extension]

            if (lang === "none" || lang === undefined) {
                let highlighted = hljs.highlightAuto(file["content"], supportedLangs)
                if (highlighted["language"] === null || highlighted["language"] === "" || highlighted["language"] === undefined) {
                    lang = "none"
                } else {
                    lang = highlighted["language"]
                }
            }

            file["lang"] = lang
            files.push(file)
        }

        setTabContent(files);
    }, [children]);

    useEffect(() => {
        window.Prism = window.Prism || {};
        Prism.manual = true;
    }, []);

    useLayoutEffect(() => {
        Prism.highlightAll({async: true});
    }, [tabContent]);

    async function copyConent() {
        try {
            await navigator.clipboard.writeText(tabContent[tab] !== undefined ? tabContent[tab]["content"] : '');
            setCopiedContent(true);
        } catch (err) {
            setCopiedContent(false);
        }
    }

    useEffect(() => {
        const timer = setTimeout(() => {
            setCopiedContent(null);
        }, 2000);
        return () => clearTimeout(timer);
    }, [copiedContent]);

    return (
        <>
            <div className={"tabContainer"}>
                {tabContent.map((file, index) => {
                    return (
                        <div className={index === tab ? "tabOuter tabSelected": "tabOuter tabNot"} key={`tab-${index}`}>
                            <div className={index === tab ? "tabBase tabSelected" : "tabBase tabNot"} onClick={() => setTab(index)}> {file["filename"]}</div>
                        </div>
                        )
                })}
            </div>
            <div className={"preContainer"}>
                <div className={"copyButton"} onClick={() => copyConent()}>{copiedContent === null ? <CopySVG /> : copiedContent === true ? <DoneSVG/> : <CloseSVG/>}</div>
                <pre className="line-numbers" style={{whiteSpace: "pre-wrap"}} suppressHydrationWarning>
                    {tabContent.map((file, index) => {
                        return <Fragment key={`codeBlock-${index}`}>
                            <code className={`language-${file["lang"]}`} style={tab !== index ? {display: "none"} : null}>{file["content"]}</code>
                        </Fragment>
                    })}
            </pre>
            </div>
        </>
    )
}