import styles from "../styles/TipModal.module.css";
import {Button} from "react-bootstrap";
import {useEffect, useState} from "react";
import cookieCutter from "cookie-cutter";

export default function TipModal() {
    const [showTip, setShowTip] = useState(true);

    useEffect(() => {
        const showCookie = cookieCutter.get("showTips");

        if (showCookie === "false") {
            setShowTip(false)
        }
    })

    function handleClick() {
        setShowTip(false);
        cookieCutter.set("showTips", false);
    }

    return (
        <>
        {showTip ?
                <div className={styles.tipModal}>
                    Welcome to the new MystBin!<br/><br/>

                    <span style={{fontSize: "0.9em"}}><b>Did you know:</b> You can change the filename and extension? Changing the extension lets you change
            the language your paste will be highlighted in. For example, for Python scripts, change the extension to .py</span>

                    <br/><br/>
                    <Button onClick={handleClick}>
                        Ok
                    </Button>
                </div>
                : null}
        </>
    )
}