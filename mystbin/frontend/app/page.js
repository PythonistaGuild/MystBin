"use client";
import {useEffect, useRef, useState} from "react";

import * as dayjs from 'dayjs';
import RelativeTime from 'dayjs/plugin/relativeTime';
import Editor from "@/app/components/editor";
import Footer from "@/app/components/footer";
import { useRouter } from 'next/navigation';
import {useCookies} from "react-cookie";
import { useSearchParams } from 'next/navigation'
import LoadingBall from "@/app/svgs/loader";

dayjs.extend(RelativeTime);


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


export default function Home() {
    const [tabContent, setTabContent] = useState([{"filename": "file.ext", "content": "", "lang": "none"}]);
    const passRef = useRef(null);
    const expireRef = useRef(null);
    const [savedPaste, setSavedPaste] = useState(null);
    const [ratelimit, setRatelimit] = useState(false);
    const [pasteError, setPasteError] = useState(false);
    const [passwordNeeded, setPasswordNeeded] = useState(false);
    const [fetched, setFetched] =useState(false);
    const [saving, setSaving] = useState(false);

    const searchParams = useSearchParams()
    const copyID = searchParams.get('copy')

    const [cookies, setCookie, removeCookie] = useCookies();
    const { push } = useRouter();

    function getLangFromName(name) {
        if (name === undefined) { return "none" }

        let extension = (/\.(\w+)$/.exec(name) || [, 'none'])[1];
        return EXTENSIONS[extension];
    }

    async function fetchPaste() {
        let URL = `${process.env.NEXT_PUBLIC_BACKEND_HOST}/paste/${copyID}`

        let password = cookies[copyID];
        if (password) {
            URL += `?password=${password}`
        }

        let response;
        try {
            response = await fetch(URL);
        } catch (error) {
            // TODO: Some sort of validation...
            return
        }

        if (response.status === 404) {
            // TODO: Some sort of validation...
            return
        }

        else if (response.status === 401) {
            setPasswordNeeded(true);
            return
        }

        else if (response.status >= 500) {
            // TODO: Some sort of validation...
            return
        }

        if (response.status === 429) {
            // TODO: Some sort of validation...
            return
        }

        const data = await response.json();
        const files = data["files"];
        let newFiles = [];


        for (let file of files) {
            newFiles.push({"filename": file.filename, "content": file.content, "lang": getLangFromName(file.filename)})
        }

        setTabContent(newFiles);
        setFetched(true);
    }

    useEffect(() => {
        if (copyID === null || copyID === "") {
            return
        }
        fetchPaste();
    }, [copyID]);


    async function savePaste() {
        if (saving) {
            return
        }

        if (tabContent.every( (val, i, arr) => val["content"] === "" )) {
            setSaving(false);
            return
        }

        setSaving(true);
        let pasteContent = {files: []};

        for (let file of tabContent) {
            if (file["content"] === "\n" || file["content"] === "") {
                continue
            }

            let temp = {"filename": file.filename, "content": file.content};
            pasteContent.files.push(temp);
        }

        if (passRef.current.value !== "") {
            pasteContent["password"] = passRef.current.value
        }

        if (expireRef.current.value !== "") {
            let current = dayjs();
            pasteContent["expires"] = current.add(expireRef.current.value, 'hour').toISOString();
        }

        // TODO: Logged in pastes...

        const URL = `${process.env.NEXT_PUBLIC_BACKEND_HOST}/paste`
        let response;
        try {
            response = await fetch(URL, {
                method: "POST",
                headers: new Headers({"Content-Type": "application/json"}),
                body: JSON.stringify(pasteContent)
            })
        } catch (err) {
            setPasteError(true);
            setSaving(false);
            return
        }

        if (response.status === 200) {
            let data = await response.json();
            let identifier = data["id"];

            setSavedPaste(identifier);
            setSaving(false);

            if (pasteContent["password"] !== undefined) {
                setCookie(identifier, pasteContent["password"], {maxAge: 3600})
            }
            return
        }

        if (response.status === 429) {
            setRatelimit(true);
            setSaving(false);
            return
        } else {
            setRatelimit(false);
        }

        if (response.status >= 200) {
            setPasteError(true);
        }

        setSaving(false);
    }

    useEffect(() => {
        if (savedPaste === null) {
            return
        }
        push(`/${savedPaste}`);
    }, [savedPaste]);

  return (
      <>
          <div className={"container"}>
              {
                  passwordNeeded ?
                      <small className={"wrongPassword"} style={{marginTop: "2rem"}}>The paste <a href={`/${copyID}`} className={"passwordFormHighlight"}>{copyID}</a> requires a password to copy. Please visit the paste and unlock it first.</small>
                      :
                      null
              }

              <div className={"navLimiter"}>
                  <div className={"navContainer"}>
                      <div className={"pasteForm"}>
                          <div className={"pasteFormItem"}>
                              <small>Optional Password:</small>
                              <input type={"text"} ref={passRef} className={"passwordPasteInput"} autoComplete="off" placeholder={"Optional Password"}/>
                          </div>
                          <div className={"pasteFormItem"}>
                              <small>Optional Expiry: (Hours)</small>
                              <input type={"number"} ref={expireRef} className={"passwordPasteInput"} autoComplete="off" placeholder={"Between 1-72"} min="0" max="72"/>
                          </div>
                          <div className={"pasteFormItem navRight navMobileOff"}>
                              <div className={"pasteSubmitButton"} onClick={savePaste}>{saving ? <LoadingBall /> : "Save Paste"}</div>
                              {ratelimit ? <small className={"wrongPassword"}>You are being rate limited. Please slow down, and try again later.</small> : null}
                              {pasteError ? <small className={"wrongPassword"}>It looks like an internal error has occurred. Please try again in a moment.</small> : null}
                          </div>
                      </div>
                  </div>
              </div>

              <div className={"innerWrapper"}>
                  <Editor copyID={copyID} tabContent={tabContent} setTabContent={setTabContent} fetched={fetched} />

                  <div className={"pasteButtonMobile navMobileOn"}>
                      <div className={"pasteSubmitButton"} onClick={savePaste}>{saving ? <LoadingBall /> : "Save Paste"}</div>
                      {ratelimit ? <small className={"wrongPassword"}>You are being rate limited. Please slow down, and try again later.</small> : null}
                      {pasteError ? <small className={"wrongPassword"}>It looks like an internal error has occurred. Please try again in a moment.</small> : null}
                  </div>

                  <Footer />
              </div>
          </div>
      </>
  )
}
