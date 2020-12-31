import { useEffect, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import CloseIcon from "@material-ui/icons/Close";
import { Toast } from "react-bootstrap";
import PasswordModal from "./PasswordModal";
import AES from "crypto-js/aes";
import Utf8 from "crypto-js/enc-utf8";

export default function EditorTabs({ initialData, encryptedPayload }) {
  const [value, setValue] = useState<Record<string, string>[]>(initialData);
  const [currTab, setCurrTab] = useState(0);
  const [charCountToast, setCharCountToast] = useState(false);
  const [passwordModal, setPasswordModal] = useState(!!encryptedPayload);
  const [shake, setShake] = useState(false);
  const [lang, setLang] = useState([]);

  useEffect(() => {
    let initialLangs = [];
    value.map(function (v) {
      if (v["title"].endsWith(".py")) {
        initialLangs.push("python");
      } else {
        initialLangs.push("none");
      }

      setLang(initialLangs);
    });
  }, [value]);

  const handlePasswordAttempt = (attempt: string) => {
    let decryptedBytes = AES.decrypt(encryptedPayload, attempt);
    try {
      let actualData = JSON.parse(decryptedBytes.toString(Utf8));
      setPasswordModal(false);
      setValue(actualData);
    } catch {
      setShake(true);
      setTimeout(function () {
        setShake(false);
      }, 500);
    }
  };

  return (
    <>
      <PasswordModal
        show={passwordModal}
        shake={shake}
        onAttempt={handlePasswordAttempt}
      />
      <div>
        <div className={styles.tabsContainer}>
          {value.map((_, i) => (
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

                  let newValue = value;
                  newValue[i]["title"] = filename.textContent;
                  setValue(newValue);

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
                  {value[i]["title"]}
                </span>
              </div>
              {value.length > 1 ? (
                <button
                  className={styles.tabsCloseButton}
                  onClick={() => {
                    let newValue = [...value];
                    let newLang = [...lang];

                    newValue.splice(i, 1);
                    newLang.splice(i, 1);
                    newLang.push("none");

                    setCurrTab(
                      currTab > 1 ? (currTab !== i ? currTab : currTab - 1) : 0
                    );

                    setLang(newLang);
                    setValue(newValue);
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
                  newValue.push({ title: "default_name.ext", content: "" });
                  setValue(newValue);
                  setCurrTab(value.length);
                }
              }}
            >
              +
            </button>
          ) : (
            <></>
          )}
        </div>

        {value.map((_, i) => (
          <div
            style={{
              display: currTab === i ? "block" : "none",
            }}
            className={"maxed"}
          >
            <MonacoEditor
              language={lang[i]}
              onChange={(_, newVal) => {
                if (newVal.length > 300000) {
                  setCharCountToast(true);
                  newVal = newVal.slice(0, 300000);
                }
                let newValue = [...value];
                newValue[i]["content"] = newVal;
                setValue(newValue);
                return `${newVal}`;
              }}
              value={value[i]["content"]}
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
