import { useRef, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import CloseIcon from "@material-ui/icons/Close";
import Toast from "react-bootstrap/Toast";

export default function EditorTabs() {
  const [value, setValue] = useState(["..."]);
  const [currTab, setCurrTab] = useState(0);
  const [lang, setLang] = useState(Array(5).fill("none"));
  const [tabNames, setTabName] = useState(Array(5).fill("default_name.ext"));
  const [charCountToast, setCharCountToast] = useState(false);

  return (
    <>
      <div>
        <div className={styles.tabsContainer}>
          {value.map((v, i) => (
            <div className={currTab === i ? styles.tabsSelected : styles.tabs}>
              <div
                onClick={() => setCurrTab(i)}
                onKeyDown={(e) => {
                  const button = e.currentTarget;

                  if (e.key == "Enter") {
                    button.blur(); // Lose focus...
                  }
                }}
                onBlur={(e) => {
                  const filename = e.currentTarget.children[0];

                  if (filename.textContent === "") {
                    filename.textContent = `default_name.ext`;
                  }

                  let newNames = tabNames;
                  newNames[i] = filename.textContent;
                  setTabName(newNames);

                  if (filename.textContent.endsWith(".py")) {
                    let langCopy = [...lang];
                    langCopy[currTab] = "python";

                    setLang(langCopy);
                  }
                }}
              >
                <span
                  contentEditable={true}
                  className={styles.tabsFilename}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      e.currentTarget.blur();
                    }
                  }}
                >
                  {tabNames[i]}
                </span>
              </div>
              {value.length > 1 ? (
                <button
                  className={styles.tabsCloseButton}
                  onClick={(event) => {
                    let newValue = [...value];
                    let newLang = [...lang];
                    let newNames = [...tabNames];

                    newValue.splice(i, 1);
                    newLang.splice(i, 1);
                    newNames.splice(i, 1);

                    newLang.push("none");
                    newNames.push("default_name.ext");

                    setCurrTab(
                      currTab > 1 ? (currTab !== i ? currTab : currTab - 1) : 0
                    );

                    setLang(newLang);
                    setValue(newValue);
                    setTabName(newNames);
                  }}
                >
                  <CloseIcon className={styles.tabsCloseButton} />
                </button>
              ) : (
                <></>
              )}
            </div>
          ))}
          {value.length <= 4 ? (
            <button
              className={styles.tabsNew}
              onClick={() => {
                if (value.length <= 4) {
                  let newValue = [...value];
                  newValue.push("");
                  setValue(newValue);
                  setCurrTab(currTab + 1);
                }
              }}
            >
              +
            </button>
          ) : (
            <></>
          )}
        </div>

        {value.map((v, i) => (
          <div
            style={{
              display: currTab === i ? "block" : "none",
            }}
            className={"maxed"}
          >
            <MonacoEditor
              language={lang[i]}
              onChange={(ev, newVal) => {
                if (newVal.length > 300000) {
                  setCharCountToast(true);
                  newVal = newVal.slice(0, 300000);
                }
                let newValue = [...value];
                newValue[i] = newVal;
                setValue(newValue);
                return `${newVal}`;
              }}
              value={value[i]}
              theme={"mystBinDark"}
              readOnly={false}
            />
          </div>
        ))}
      </div>

      <Toast
        className={styles.maxCountToast}
        onClose={() => setCharCountToast(false)}
        show={charCountToast}
        delay={5000}
        autohide
      >
        <Toast.Header className={styles.maxCountToastHeader}>
          <strong className="mr-auto">Max Character Count</strong>
          <small>Max count: 300,000</small>
        </Toast.Header>
        <Toast.Body>
          You've reached the max character count for this file.
        </Toast.Body>
      </Toast>
    </>
  );
}
