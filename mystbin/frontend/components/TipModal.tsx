import styles from "../styles/TipModal.module.css";
import { Button } from "react-bootstrap";
import { useEffect, useState } from "react";
import cookieCutter from "cookie-cutter";

export default function TipModal() {
  const [showTip, setShowTip] = useState(true);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    const showCookie = cookieCutter.get("showTips");

    if (showCookie === "false") {
      setShowTip(false);
    }
  });

  function handleClick() {
    setShowTip(false);

    const date = new Date();
    date.setDate(date.getDate() + 14);
    cookieCutter.set("showTips", false, { expires: date });
  }

  function handleChange() {
    if (tab + 1 === tabs.length) {
      setTab(0);
    }

    else {
      setTab(tab + 1)
    }
  }

  const tabs = [
      'You can change the filename and extension? Changing the extension lets you change the language your paste will be highlighted in. For example, for Python scripts, change the extension to .py',
      'You can now Drag and Drop named files into the editor to copy it\'s contents, name and file extension.',
      'You can now add images to your paste files. Click on + symbol on your file tab to add an image.',
  ]

  return (
    <>
      {showTip ? (
        <div className={styles.tipModal}>
          Welcome to the new MystBin!
          <br />
          <br />
          <span style={{ fontSize: "0.9em" }}>
            <b>Did you know:</b><br/>{tabs[tab]}
          </span>
          <br />
          <br />
          <div className={styles.bottomButtons}>
            <Button className={styles.closeButton} onClick={handleClick}>Ok</Button>
            <Button className={styles.nextButton} onClick={handleChange}>Next</Button>
          </div>
        </div>
      ) : null}
    </>
  );
}
