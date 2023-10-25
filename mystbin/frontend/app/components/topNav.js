"use client";

import { useTheme } from 'next-themes'
import LogoSmall from "@/app/svgs/logoSmallSVG"
import {useEffect, useState, useRef} from "react";
import ThemeSVG from "@/app/svgs/themeSVG";
import SunSVG from "@/app/svgs/sunSVG";
import MoonSVG from "@/app/svgs/moonSVG";
import DoneSVG from "@/app/svgs/doneSVG";
import ElectricCarSVG from "@/app/svgs/evSVG";


const themeMap = [
    {
        "name": "light",
        "display": "Light Theme",
        "svg": <SunSVG />
    },
    {
        "name": "dark",
        "display": "Dark Theme",
        "svg": <MoonSVG />
    },
    {
        "name": "neo",
        "display": "Neo Theme",
        "svg": <ElectricCarSVG />
    },
]


export default function TopNav({children}) {
    const { theme, setTheme, resolvedTheme} = useTheme();

    const [updatedTheme, setUpdatedTheme] = useState("");
    const [themeTrigger, setThemeTrigger] = useState(false);
    const menuRef = useRef(null);
    const menuContainerRef = useRef(null);


    const handleClickOutside = (event) => {
        if (menuRef.current && menuRef.current.contains(event.target)) {
        }

        else if (menuContainerRef.current && !menuContainerRef.current.contains(event.target)) {
            setThemeTrigger(false);
        }
    };

    function handleContainer(el) {
        if (el === "svg") {
            setThemeTrigger(!themeTrigger)
        }
        else if (el === "container") {}
    }

    useEffect(() => {
        document.addEventListener('click', handleClickOutside, true);
        return () => {
            document.removeEventListener('click', handleClickOutside, true);
        };
    }, []);

    useEffect(() => {
        setUpdatedTheme(resolvedTheme);
    }, [resolvedTheme]);

    return (
        <div className={"topNavContainer justSB alignCent"}>
            <a className={"topNavLogo"} href={`/`}>
                <LogoSmall className={"logoSmall"} />
                <span>MystBin</span>
            </a>

            <div className={"themeMenuContainer"} onClick={() => handleContainer("container")} ref={menuContainerRef}>
                <ThemeSVG onClick={() => handleContainer("svg")} />

                <div className={"themeMenu"} style={!!themeTrigger ? {display: "flex"} : {display: "none"}} ref={menuRef}>
                    {themeMap.map((theme_, i) => {
                        return <span
                            className={theme_["name"] === updatedTheme ? "themeMenuDisabled" : null}
                            onClick={() => setTheme(theme_["name"])}
                            key={`theme-${i}`}>
                            {theme_["svg"]}{theme_["display"]}{theme_["name"] === updatedTheme ? <DoneSVG style={{opacity: 0.7, fill: "currentColor", color: "var(--link-colour)"}} /> : ""}
                        </span>
                    })}
                </div>
            </div>

            <div id={"loginButton"}>
                Login
            </div>
        </div>
    )
}