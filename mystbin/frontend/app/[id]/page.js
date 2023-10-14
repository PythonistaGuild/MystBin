"use client";
import dynamic from 'next/dynamic'

import {useEffect, useRef, useState} from "react";

import '@/prism/prism.css';
import { useCookies } from 'react-cookie';

import * as dayjs from 'dayjs';
import RelativeTime from 'dayjs/plugin/relativeTime';
import UTC from 'dayjs/plugin/utc'
import TimeZone from 'dayjs/plugin/timezone'
dayjs.extend(RelativeTime);
dayjs.extend(UTC);
dayjs.extend(TimeZone);

import LockSVG from "@/app/svgs/lockSVG";
import ShareSVG from "@/app/svgs/shareSVG";
import DownloadSVG from "@/app/svgs/downloadSVG";
import NewSVG from "@/app/svgs/newSVG";
import DoneSVG from "@/app/svgs/doneSVG";
import CloseSVG from "@/app/svgs/closeSVG";

import JSZip from "jszip";
import Footer from "@/app/components/footer";
import Image from "next/image";

const CodeBlock = dynamic(() => import('../components/codeBlock'), { ssr: false })


export default function Home({ params }) {
    const pasteID = params.id;

    const [tabContent, setTabContent] = useState([]);
    const [createdAt, setCreatedAt] = useState('');
    const [expiresAt, setExpiresAt] = useState(null);
    const [copiedUrl, setCopiedUrl] = useState(null);
    const [fourOhFour, setFourOhFour] = useState(false);
    const [preLoad,setPreLoad] = useState(false);
    const [passProtected, setPassProtected] = useState(null);
    const [wrongPassword,setWrongPassword] = useState(false);
    const [oldPassword, setOldPassword] = useState(null);
    const passRef = useRef(null);
    const [cookies, setCookie, removeCookie] = useCookies();
    let storedPass = cookies[pasteID];

    const [ratelimit, setRatelimit] = useState(false);
    const [internalError, setInternalError] = useState(false);


    async function fetchPaste(password) {
        if (!password && storedPass) {
            password = storedPass
        }

        setWrongPassword(false);

        let URL = `${process.env.NEXT_PUBLIC_BACKEND_HOST}/paste/${pasteID}`
        if (password) {
            URL += `?password=${password}`
        }

        let response;
        try {
            response = await fetch(URL);
        } catch (error) {
            setInternalError(true);
            return
        }

        if (response.status === 404) {
            setFourOhFour(true);
            return
        }

        else if (response.status === 401) {
            setPassProtected(true);
            if (password) {
                setWrongPassword(true);
            }

            if (storedPass) {
                removeCookie(pasteID);
            }

            return
        }
        else if (response.status >= 500) {
            setInternalError(true);
            return
        }

        if (response.status === 429) {
            setRatelimit(true)
            return
        }
        else {
            setRatelimit(false);
        }

        if (password !== undefined) {
            setCookie(pasteID, password, {maxAge: 3600})
            setPassProtected(false);
        }

        const data = await response.json();
        const files = data["files"];

        setExpiresAt(data["expires"]);
        setCreatedAt(data["created_at"]);
        setTabContent(files);
        setPreLoad(true)
    }

    async function fetchPastePass(e) {
        e.preventDefault();

        let password = passRef.current.value;
        if (!password) {
            return
        }

        if (password === oldPassword) {
            return
        }

        setOldPassword(password);
        await fetchPaste(password);
    }

    useEffect( () => {
        fetchPaste();
    }, []);

    function shareSelect(e) {
        e.target.select();
    }

    useEffect(() => {
        const timer = setTimeout(() => {
            setCopiedUrl(null);
        }, 2000);
        return () => clearTimeout(timer);
    }, [copiedUrl]);

    async function copyURL() {
        try {
            await navigator.clipboard.writeText(`${process.env.NEXT_PUBLIC_FRONTEND_HOST}/${pasteID}`);
            setCopiedUrl(true);
        } catch (err) {
            setCopiedUrl(false);
        }
    }

    async function downloadPaste(){
        const zip = new JSZip();
        let seen = [];

        for (let file of tabContent) {
            let name = file['filename'];
            seen.push(name);

            let seenCount = seen.filter(function(value){
                return value === name;
            }).length - 1
            if (seenCount >= 1) {
                name = `(${seenCount})${name}`
            }

            const blob = new Blob([file['content']], {type: 'text'})
            zip.file(name, blob);
        }

        const zipData = await zip.generateAsync({
            type: "blob",
            streamFiles: true,
        });

        const link = document.createElement("a");
        link.href = window.URL.createObjectURL(zipData);
        link.download = `mystbin_${pasteID}.zip`;
        link.click();
    }

    return (
        <>
            {internalError ?
                <div className={"container"}>
                    <div className={"navLimiter"}>
                        <div className={"navContainer"}>
                        </div>
                    </div>

                    <div className={"innerWrapper"}>
                        <div className={"fourOhFour"}>
                            <h1>Internal API Error</h1>
                            <small className={"wrongPassword"}>Uh-oh, looks like our servers are having some troubles. Please try again later.</small>
                            <Image className={"errorImage"} src={"/internal.png"} alt={"Server Error Robot"} width={100} height={100} />
                        </div>
                        <Footer />
                    </div>
                </div>
                :
                ratelimit > true ?
                <div className={"container"}>
                    <div className={"navLimiter"}>
                        <div className={"navContainer"}>
                        </div>
                    </div>

                    <div className={"innerWrapper"}>
                        <div className={"fourOhFour"}>
                            <h1>429</h1>
                            <p className={"wrongPassword"}>You are being rate limited. Please slow down, and try again later.</p>
                        </div>
                        <Footer />
                    </div>
                </div>
                :
                fourOhFour === true ?
                <div className={"container"}>
                    <div className={"navLimiter"}>
                        <div className={"navContainer"}>
                        </div>
                    </div>

                    <div className={"innerWrapper"}>
                        <div className={"fourOhFour"}>
                            <h1>404 - Page Not Found</h1>
                            <small className={"wrongPassword"}>The paste <span>{pasteID}</span> could not be found :(</small>
                            <Image className={"errorImage"} src={"/ghost.png"} alt={"Server Error Robot"} width={100} height={100} />
                            <a href={"/"} style={{marginTop: "2rem"}}><small>Return home</small></a>
                        </div>
                        <Footer />
                    </div>
                </div>
                : preLoad === true ?
                    <div className={"container"}>
                        <div className={"navLimiter"}>
                            <div className={"navContainer"}>
                                <div className={"flexRow gap2 alignCent"}>
                                    <div>
                                        {/* TODO: Add Username login stuff here... */}
                                        <span className={"navMetaNameContainer"}><a href={`/`}><h3 className={"navHeader"}></h3></a><a href={`/${pasteID}`}><h3 className={"navHeader"}>/{pasteID}</h3></a></span>
                                        <div className={"flexCol times"}>
                                            <span className={"navCreated"}>Created {dayjs().to(dayjs.utc(createdAt))}...</span>
                                            {expiresAt ? <span className={"navCreated"}>Expires {dayjs().to(dayjs.utc(expiresAt))}...</span> : null}
                                        </div>
                                    </div>
                                    {passProtected === false ? <div className={"label"} style={{alignSelf: "center"}}><LockSVG />Protected</div> : null}
                                </div>

                                <div className={"navRight flexCol gap1 alignEnd"} id={"navShares"}>
                                    <div className={"flexRow gap1 alignEnd height2"}>
                                        <a className={"editButton"} href={`/?copy=${pasteID}`}><NewSVG />Copy and Edit</a>
                                    </div>

                                    <div className={"flexRow gap1 alignEnd height2"}>
                                        <div className={"shareContainer"}>
                                            <input readOnly={true} value={`${process.env.NEXT_PUBLIC_FRONTEND_HOST}/${pasteID}`} type={"text"} onFocus={shareSelect}/>
                                            <div className={"shareButton"} onClick={() => copyURL()}>{copiedUrl === null ? <ShareSVG /> : copiedUrl === true ? <DoneSVG/> : <CloseSVG/>}</div>
                                        </div>
                                        <div className={"downloadButton"} onClick={() => downloadPaste()}>Download <DownloadSVG /></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className={"innerWrapper"}>
                            <CodeBlock>{tabContent}</CodeBlock>
                            <Footer />
                        </div>
                    </div>
                    : passProtected === true ?
                        <div className={"container"}>
                            <div className={"navLimiter"}>
                                <div className={"navContainer"}>
                                </div>
                            </div>

                            <div className={"innerWrapper"}>
                                <div className={"passwordForm"}>
                                    <h1>Protected</h1>
                                    <div>
                                        <p>The paste <span className={"passwordFormHighlight"}>{pasteID}</span> has been password protected.</p>
                                        <small>Please enter the password to continue:</small>
                                    </div>
                                    <form onSubmit={fetchPastePass}>
                                        <input type={"password"} ref={passRef} className={"passwordFormInput"} autoComplete="off"/>
                                        <div className={"passwordFormSubmit"} onClick={fetchPastePass}>Submit</div>
                                        {ratelimit ? <small className={"wrongPassword"}>You are being rate limited. Please slow down, and try again later.</small> : null}
                                        {wrongPassword ? <small className={"wrongPassword"}>You entered the wrong password. Please try again.</small> : null}
                                    </form>
                                </div>
                                <Footer />
                            </div>
                        </div>
                        : null
            }
        </>
    )
}
